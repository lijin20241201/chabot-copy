import os
import re
import threading
import time
from asyncio import CancelledError
# concurrent.futures 提供了一个高级的接口，用来处理并行计算
from concurrent.futures import Future, ThreadPoolExecutor
from bridge.context import *
from bridge.reply import *
from channel.channel import Channel
from common.dequeue import Dequeue
from common import memory
from plugins import *

try:
    from voice.audio_convert import any_to_wav
except Exception as e:
    pass
# max_workers=8：这个参数指定了线程池中可以同时运行的最大线程数。
handler_pool = ThreadPoolExecutor(max_workers=8) 
# 一个 ChatChannel 实例 ：表示一个消息通道的实例，它负责处理消息的接收和发送。
# 多个 session_id ：表示多个会话的标识，每个会话可能对应一个用户或一个群聊。
# 一个 ChatChannel 实例可能会处理多个会话，每个会话都有自己的 session_id。通过使用字典来存储 session_id 和 
# futures 对象，ChatChannel 可以管理多个会话的并发处理。
# ChatChannel 类中的方法和处理逻辑是所有特定消息通道（如微信、Telegram、Slack等）可以共用的逻辑。ChatChannel 
# 提供了与具体消息通道无关的通用处理功能，而具体的消息通道类（如 WeChatChannel、TelegramChannel 等）可以继承 
# ChatChannel 并实现各自特定的逻辑。
# 您可以创建多个 ChatChannel 实例，每个实例都可以看作是一个独立的机器人。
# 这些实例可以共享相同的名字和ID，表示它们作为一个群体共同处理消息。
# 每个 ChatChannel 实例管理自己的会话（session_id），并使用线程池和信号量来控制并发处理。
# 这种设计确保每个会话在同一时刻只有一个消息被处理，避免了并发冲突。
class ChatChannel(Channel):
    # 该属性用于存储登录的用户名，通常是机器人的用户名。
    name = None  
    # 该属性用于存储登录的用户ID，通常是机器人的用户ID。
    user_id = None 
    # 用于存储异步操作的结果。它是一个类属性，因此所有 ChatChannel 类的实例都会共享这个字典。
    futures = {}
    # 将每个会话与消息队列和信号量关联。它是类属性，因此所有 ChatChannel 的实例都共享这个字典。
    sessions = {}  
    # lock：这是一个线程锁，用于确保对共享资源（如 sessions）的线程安全访问。它也是类属性
    lock = threading.Lock() 
    # 每个 ChatChannel 实例都生成一个线程，这个线程会不断地遍历所有的 session_id，并处理每个会话对应的消息。
    # ChatChannel 实际上充当了一个消息分发和处理的中枢。
    def __init__(self):
       # 初始化一个后台线程，执行 consume 方法。
        _thread = threading.Thread(target=self.consume)
        # 将线程设置为守护线程（daemon thread）。
        # 守护线程会在主线程退出时自动终止，而非守护线程则会阻止程序的退出，必须等到线程运行结束。
        _thread.setDaemon(True)
        _thread.start() # 启动线程后，线程进入 就绪状态，等待 CPU 调度。
    def _compose_context(self, ctype: ContextType, content, **kwargs):
        # 创建一个新的 Context 对象
        context = Context(ctype, content)
        context.kwargs = kwargs
        # 检查 context的kwargs 中是否包含键 "origin_ctype"。如果不包含，则将其设置为当前的 ctype，确保在
        # 后续处理中可以正确地使用 origin_ctype。
        if "origin_ctype" not in context:
            context["origin_ctype"] = ctype
        # 检查 context的kwargs中是否包含键'receiver',第一次不包含'receiver'
        first_in = "receiver" not in context
        if first_in: # 第一次时 
            config = conf()
            cmsg = context["msg"] 
            user_data = conf().get_user_data(cmsg.from_user_id) # 根据发送者id获取用户输入数据
            context["openai_api_key"] = user_data.get("openai_api_key")
            context["gpt_model"] = user_data.get("gpt_model")
            # 如果是群聊消息，处理群聊相关的逻辑
            if context.get("isgroup", False):
                group_name = cmsg.other_user_nickname # 群名称
                group_id = cmsg.other_user_id # 群id
                # 群名称白名单列表：是一个配置项，包含了允许机器人回复的群聊名称（或者说群组的昵称）。这个列表中的群聊，机器人才
                # 会处理其发来的消息。
                group_name_white_list = config.get("group_name_white_list", []) 
                # 群名称关键字白名单列表：这个列表包含了一些关键字，只要群名称中包含这些关键字，该群的消息就会被机器人回复。它提供了
                # 比直接匹配群名称白名单更灵活的方式。群聊的名称只要包含关键字，就会被认为是有效的群组。
                group_name_keyword_white_list = config.get("group_name_keyword_white_list", [])
                # any() 函数接受一个可迭代对象（如列表、元组等），如果可迭代对象中的任何一个元素为 True，则 any() 返回 True；否则返回 False。
                # 这里传入的列表包含了 三个条件：
                # group_name in group_name_white_list：判断群名称是否在群名称白名单列表中。
                # "ALL_GROUP" in group_name_white_list：判断是否存在一个特殊的白名单项 "ALL_GROUP"，这个值表示所有群组都可以被允许。
                # 最后一个条件：检查群名称是否包含在群名称关键字白名单列表中的某个关键字。
                if any(
                    [
                        group_name in group_name_white_list,
                        "ALL_GROUP" in group_name_white_list,
                        check_contain(group_name, group_name_keyword_white_list),
                    ]
                ):
                    # group_chat_in_one_session 是一个配置项，用来定义哪些群聊应该在同一个会话中进行处理。这个配置通常用于限制
                    # 在特定群组内，所有的消息都可以使用相同的会话 ID。
                    # 这个配置项是一个包含群组名称的列表，表示这些群组的消息会被视为属于同一个会话进行处理
                    group_chat_in_one_session = conf().get("group_chat_in_one_session", [])
                    # 这一行设置 session_id 为 cmsg.actual_user_id，即群消息中的实际发送者ID
                    # 这里的 session_id 可能用于跟踪与该用户相关的所有消息，确保机器人能够在多轮对话中维持会话上下文。
                    # 在一个时刻多个用户发送消息时，每个用户的 session_id 都是独立的，即每个用户会有一个自己的 session_id。在这种情
                    # 况下，系统不会将不同用户的消息合并为一个会话 ID，而是会根据每个用户的 实际用户 ID（cmsg.actual_user_id） 来为每个
                    # 用户创建不同的会话 ID
                    session_id = cmsg.actual_user_id
                    # 检查当前群名称是否在配置项group_chat_in_one_session 列表中。也就是说，如果这个群被列入该配置项中，表示所有在
                    # 这个群里的消息应该被视为属于同一个会话。
                    # "ALL_GROUP" in group_chat_in_one_session：这是一个特殊的条件，检查 group_chat_in_one_session 中是否
                    # 包含 "ALL_GROUP"。如果包含，意味着所有群聊中的消息都应该共享同一个会话 ID。也就是说，无论是哪一个群的消息，都会使
                    # 用相同的 session_id。
                    if any(
                        [
                            group_name in group_chat_in_one_session,
                            "ALL_GROUP" in group_chat_in_one_session,
                        ]
                    ):
                        # session_id = group_id 将 会话 ID 设置为群组 ID，也就是说，在该群中的所有消息都会共享同一个 session_id，
                        # 而不是基于发送者的用户 ID。这样做的目的是让同一个群聊中的所有消息被视为同一个会话，方便机器人进行群体回复。
                        # 同一个群聊内的消息共享 session_id：这样做的好处是，群内所有人的消息都会被视为同一个会话，机器人可以根据群组 ID 
                        # 来统一管理对话状态，并做出一致的回应。特别是在群聊中，机器人能够基于 群组 ID 进行群体对话管理，而不是对每个用户进
                        # 行单独的会话管理。
                        session_id = group_id
                # 不需要回复，groupName不在白名单中，这种情况不需要机器人回复
                else:
                    logger.debug(f"No need reply, groupName not in whitelist, group_name={group_name}")
                    return None
                context["session_id"] = session_id # 设置session_id
                context["receiver"] = group_id # 设置receiver
            # 如果是私聊消息，则使用私聊的 other_user_id 来设置会话 ID 和接收者（receiver）。
            else:
                context["session_id"] = cmsg.other_user_id 
                context["receiver"] = cmsg.other_user_id
            # 所有监听ON_RECEIVE_MESSAGE的插件会按优先级处理这个e_context,并可以根据需要修改它。
            e_context = PluginManager().emit_event(EventContext(Event.ON_RECEIVE_MESSAGE, {"channel": self, "context": context}))
            context = e_context["context"]
            # 如果事件传播行为是 BREAK_PASS(事件结束) 或者 context 是 None，返回 context
            if e_context.is_pass() or context is None:
                return context
            # 如果消息是机器人自己发送的且配置中不允许处理自己发送的消息，跳过处理
            if cmsg.from_user_id == self.user_id and not config.get("trigger_by_self", True):
                logger.debug("[chat_channel]self message skipped")
                return None
        # 处理文本消息内容
        if ctype == ContextType.TEXT:
            # 如果是第一次进入此方法并且内容中包含引用消息(对之前消息的引用)的标志，则跳过处理
            if first_in and "」\n- - - - - - -" in content:  
                logger.debug(content) # 输出当前内容到日志
                # 输出跳过处理的日志
                logger.debug("[chat_channel]reference query skipped")
                return None # 跳过此次处理，返回 None
            # 获取黑名单中的昵称列表
            nick_name_black_list = conf().get("nick_name_black_list", [])
            if context.get("isgroup", False):  # 如果是群聊消息，处理群聊相关的逻辑
                # match_prefix检查content是否包含@bot这样的前缀,match_contain检查是否包含这些关键字
                match_prefix = check_prefix(content, conf().get("group_chat_prefix"))
                match_contain = check_contain(content, conf().get("group_chat_keyword"))
                flag = False # 标志位，是否触发了机器人的回复
                # 如果消息接收者不是实际发送者
                # 在 群聊的场景下，如果是机器人发送的消息,机器人接收,这个情况下才可能相同
                if context["msg"].to_user_id != context["msg"].actual_user_id:
                    # 如果匹配到前缀或关键字，说明触发了机器人回复
                    # 在这个条件判断下，通常表示 群聊中的用户与机器人之间的互动，即用户希望机器人进行回复。消息的发送者（
                    # actual_user_id）是群聊中的一个用户，接收者（to_user_id）是机器人，或者群聊的机器人会被触发响应。
                    if match_prefix is not None or match_contain is not None:
                        flag = True
                        # 1 是 replace() 方法的 替换次数参数，表示只替换第一个匹配的部分。这样做的目的是 去掉消息中的前缀，
                        # 比如 @bot，但只去掉 第一个 出现的前缀，以免误删消息中的其他 @bot（如果存在的话）。
                        if match_prefix:
                            content = content.replace(match_prefix, "", 1).strip() 
                    #  如果消息中包含@某人
                    if context["msg"].is_at:
                        nick_name = context["msg"].actual_user_nickname # 实际发送者的昵称
                        if nick_name and nick_name in nick_name_black_list:
                            # 如果昵称在黑名单中，则忽略该消息
                            logger.warning(f"[chat_channel] Nickname {nick_name} in In BlackList, ignore")
                            return None
                        logger.info("[chat_channel]receive group at") # 记录收到群聊 @ 的日志
                        # 如果配置没有关闭群聊时 @bot 的触发，则设置标志位为 True
                        if not conf().get("group_at_off", False):
                            flag = True
                        self.name = self.name if self.name is not None else ""  # 确保 self.name 已经赋值
                        # 匹配@self.name(一般是bot),后面跟空格或四分之一空格的模式
                        # 如果 self.name = "chatbot\u2005"（四分之一空格），re.escape(self.name) 会返回 chatbot\u2005，
                        # 而不是将它转化为 \u2005 形式。
                        pattern = f"@{re.escape(self.name)}(\u2005|\u0020)" 
                        # re.sub 会扫描 content 中的文本，找到所有符合 pattern 的部分，并用空字符串 r"" 将它们替换掉，
                        # 最终返回替换后的结果 subtract_res。
                        subtract_res = re.sub(pattern, r"", content) 
                        # at_list 通常是指被@的用户的昵称列表，也就是说，at_list 中保存了所有在当前消息中提到（@）的群成员的昵称。
                        # 如果消息中有@群内其他人的情况，它会删除所有类似 @user 后跟空格的提及部分。
                        if isinstance(context["msg"].at_list, list):
                            for at in context["msg"].at_list:
                                pattern = f"@{re.escape(at)}(\u2005|\u0020)"
                                subtract_res = re.sub(pattern, r"", subtract_res)
                        # context["msg"].self_display_name 指的是 机器人在当前群聊中的显示昵称。
                        # 这里移除content中@机器人昵称的部分
                        if subtract_res == content and context["msg"].self_display_name:
                            pattern = f"@{re.escape(context['msg'].self_display_name)}(\u2005|\u0020)"
                            subtract_res = re.sub(pattern, r"", content)
                        content = subtract_res # 更新content会去除@后的部分
                # 虽然接收到语音消息，但由于没有触发机器人回复，机器人 不会回复，并且通过日志提示这一点。
                if not flag:
                    if context["origin_ctype"] == ContextType.VOICE:
                        logger.info("[chat_channel]receive group voice, but checkprefix didn't match")
                    return None  
            else:  # 私聊的情况
                nick_name = context["msg"].from_user_nickname # 发送者昵称
                # 如果发送消息的用户在黑名单里,会被忽略
                if nick_name and nick_name in nick_name_black_list:
                    logger.warning(f"[chat_channel] Nickname '{nick_name}' in In BlackList, ignore")
                    return None
                # 检查单聊消息是否匹配前缀
                match_prefix = check_prefix(content, conf().get("single_chat_prefix", [""]))
                if match_prefix is not None:  # 判断如果匹配到自定义前缀，则返回过滤掉前缀+空格后的内容
                    content = content.replace(match_prefix, "", 1).strip() # 去掉匹配到的前缀
                elif context["origin_ctype"] == ContextType.VOICE: # 如果源消息是私聊的语音消息，允许不匹配前缀，放宽条件
                    pass
                else:
                    return None # 如果没有匹配到前缀，且不是语音消息，则不回复
            content = content.strip() # 去除内容前后的空白字符
            # 检查消息是否包含图像生成的前缀(画)
            img_match_prefix = check_prefix(content, conf().get("image_create_prefix",[""])) 
            if img_match_prefix:
                content = content.replace(img_match_prefix, "", 1) # 移除图像生成命令前缀
                context.type = ContextType.IMAGE_CREATE # 设置消息类型为图像生成
            else:
                context.type = ContextType.TEXT # 否则保持为文本消息
            context.content = content.strip() # 更新消息内容，去除空格
            # 回复类型的设置：如果消息上下文中没有设置 desire_rtype（期望的回复类型），并且配置允许语音回复（always_reply_voice）
            # ，则将期望的回复类型设置为语音（ReplyType.VOICE）。
            if "desire_rtype" not in context and conf().get("always_reply_voice") and ReplyType.VOICE not in self.NOT_SUPPORT_REPLYTYPE:
                context["desire_rtype"] = ReplyType.VOICE  # 设置期望的回复类型为语音
        # 处理语音消息的回复类型：对于语音消息，如果没有设置期望的回复类型，并且配置允许语音回复，则将 desire_rtype 设置为语音
        elif context.type == ContextType.VOICE:
            if "desire_rtype" not in context and conf().get("voice_reply_voice") and ReplyType.VOICE not in self.NOT_SUPPORT_REPLYTYPE:
                context["desire_rtype"] = ReplyType.VOICE # 设置语音回复类型
        return context
    # 处理消息
    def _handle(self, context: Context):
        # 如果 context 是 None 或者 context 的内容为空，直接返回，不进行处理
        if context is None or not context.content: 
            return
        # 记录调试信息，表示准备处理 context
        logger.debug("[chat_channel] ready to handle context: {}".format(context))
        # 生成回复的步骤，根据 context 生成一个 reply 对象
        reply = self._generate_reply(context)
        # 记录调试信息，表示准备装饰 reply
        logger.debug("[chat_channel] ready to decorate reply: {}".format(reply))
        # 包装 reply 的步骤，如果 reply 存在且有内容，则进行装饰
        if reply and reply.content:
            reply = self._decorate_reply(context, reply)
            # 发送 reply 的步骤，将装饰好的 reply 发送出去
            self._send_reply(context, reply)
    
    def _generate_reply(self, context: Context, reply: Reply = Reply()) -> Reply:
        # 查看当前事件对应的监听插件，并调用它们的事件处理器对 e_context 进行处理
        e_context = PluginManager().emit_event(
            EventContext( 
                Event.ON_HANDLE_CONTEXT, # 定义事件类型为对消息进行预处理
                {"channel": self, "context": context, "reply": reply}, # 当前事件的上下文数据（包含通道、消息和回复）
            )
        )
        # e_context["reply"] 是事件触发后的返回结果，也就是经过插件事件处理后的 reply
        reply = e_context["reply"]
        # 如果当前事件上下文的事件传播行为不是 BREAK_PASS
        # if not e_context.is_pass(): 后面的代码块就是默认的事件处理逻辑，它根据 context.type 处理不同类型的消息。
        if not e_context.is_pass():
            # 打印日志，记录消息类型和消息内容
            logger.debug("[chat_channel] ready to handle context: type={}, content={}".format(context.type, context.content))
            # 如果消息类型是文本消息或创建图片命令
            if context.type == ContextType.TEXT or context.type == ContextType.IMAGE_CREATE: 
                 # 设置消息的通道属性
                context["channel"] = e_context["channel"]
                # 调用父类的构建回复方法（query, context），深层调用聊天机器人的回复功能
                reply = super().build_reply_content(context.content, context)
            # 如果消息类型是语音消息（ContextType.VOICE）
            elif context.type == ContextType.VOICE:  
                # 获取语音消息内容，并进行准备
                cmsg = context["msg"]
                cmsg.prepare()
                # 将文件路径转换为 .wav 格式，调用 any_to_wav() 方法进行转换
                file_path = context.content
                # os.path.splitext用于将文件路径拆分为文件名和扩展名两部分。
                wav_path = os.path.splitext(file_path)[0] + ".wav"
                try:
                    any_to_wav(file_path, wav_path)
                except Exception as e:  # 转换失败时，直接使用原始的 mp3 文件路径
                    logger.warning("[chat_channel]any to wav error, use raw path. " + str(e))
                    wav_path = file_path
                # 使用父类方法进行语音识别，将音频文件转换为文字回复
                reply = super().build_voice_to_text(wav_path)
                # 删除临时的音频文件（原始文件和转换后的文件）
                try:
                    os.remove(file_path)
                    if wav_path != file_path:
                        os.remove(wav_path)
                except Exception as e:
                    pass
                    # logger.warning("[chat_channel]delete temp file error: " + str(e))
                # 如果识别得到的是文本类型的回复（ReplyType.TEXT），则递归调用 _generate_reply() 生成新的回复
                # 当通过语音识别生成文本回复时，系统需要对这个新的文本内容进行进一步的处理。_compose_context() 负
                # 责根据新的文本生成一个新的上下文（context），然后递归调用 _generate_reply() 进行后续处理。
                if reply.type == ReplyType.TEXT:
                    new_context = self._compose_context(ContextType.TEXT, reply.content, **context.kwargs)
                    if new_context:
                        reply = self._generate_reply(new_context)
                    else:
                        return
            # 如果消息类型是图片消息（ContextType.IMAGE）
            elif context.type == ContextType.IMAGE:  
                # 将图片消息保存在 memory.USER_IMAGE_CACHE 中
                memory.USER_IMAGE_CACHE[context["session_id"]] = {
                    "path": context.content,
                    "msg": context.get("msg")
                }
            # 如果消息类型是分享消息（ContextType.SHARING）
            elif context.type == ContextType.SHARING:  
                # 当前没有定义默认的处理逻辑，直接跳过
                pass
            # 如果消息类型是函数调用或文件消息（ContextType.FUNCTION 或 ContextType.FILE）
            elif context.type == ContextType.FUNCTION or context.type == ContextType.FILE: 
                pass
            # 如果遇到未知类型的 context.type
            else: # 打印警告日志，并直接返回
                logger.warning("[chat_channel] unknown context type: {}".format(context.type))
                return
        # 返回生成的 reply。如果 e_context.is_pass() 返回 True，表示没有修改之前的 reply，否则返回事件处理后修改过的 reply
        return reply

    def _decorate_reply(self, context: Context, reply: Reply) -> Reply:
        # 如果回复存在且回复类型不为空
        if reply and reply.type:
            # 调用监听当前类型的事件的插件的事件处理器对e_context处理
            e_context = PluginManager().emit_event(
                EventContext(
                    Event.ON_DECORATE_REPLY, # 事件类型:对回复装饰
                    {"channel": self, "context": context, "reply": reply},
                )
            )
            # 更新回复对象，使用事件处理后的回复
            reply = e_context["reply"]
            desire_rtype = context.get("desire_rtype") # 获取期望的回复类型
            # 如果事件传播没有被停止(传播行为不是BREAK_PASS)，并且回复类型有效
            if not e_context.is_pass() and reply and reply.type:
                # 如果回复类型不支持，记录错误并修改回复类型为错误类型
                if reply.type in self.NOT_SUPPORT_REPLYTYPE:
                    logger.error("[chat_channel]reply type not support: " + str(reply.type))
                    reply.type = ReplyType.ERROR
                    reply.content = "不支持发送的消息类型: " + str(reply.type)
                 # 如果回复类型是文本
                if reply.type == ReplyType.TEXT:
                    reply_text = reply.content
                     # 如果期望的回复类型是语音并且支持语音回复
                    if desire_rtype == ReplyType.VOICE and ReplyType.VOICE not in self.NOT_SUPPORT_REPLYTYPE:
                        reply = super().build_text_to_voice(reply.content)
                        return self._decorate_reply(context, reply) # 递归调用进行语音回复处理
                    # 处理群聊回复前缀/后缀
                    if context.get("isgroup", False):
                        if not context.get("no_need_at", False):
                            reply_text = "@" + context["msg"].actual_user_nickname + "\n" + reply_text.strip()
                        reply_text = conf().get("group_chat_reply_prefix", "") + reply_text + conf().get("group_chat_reply_suffix", "")
                    else:
                        # 处理单聊回复前缀/后缀
                        reply_text = conf().get("single_chat_reply_prefix", "") + reply_text + conf().get("single_chat_reply_suffix", "")
                    reply.content = reply_text  # 设置最终的回复文本内容
                 # 如果回复类型是错误或信息类型
                elif reply.type == ReplyType.ERROR or reply.type == ReplyType.INFO:
                    reply.content = "[" + str(reply.type) + "]\n" + reply.content  # 包装错误或信息内容
                # 对于其他文件、音频、视频等类型，暂时不做处理
                elif reply.type == ReplyType.IMAGE_URL or reply.type == ReplyType.VOICE or reply.type == ReplyType.IMAGE or reply.type == ReplyType.FILE or reply.type == ReplyType.VIDEO or reply.type == ReplyType.VIDEO_URL:
                    pass
                # 对于未知的回复类型，记录错误
                else:
                    logger.error("[chat_channel] unknown reply type: {}".format(reply.type))
                    return
            # 如果期望的回复类型与当前回复类型不匹配，记录警告
            if desire_rtype and desire_rtype != reply.type and reply.type not in [ReplyType.ERROR, ReplyType.INFO]:
                logger.warning("[chat_channel] desire_rtype: {}, but reply type: {}".format(context.get("desire_rtype"), reply.type))
            return reply # 返回最终的回复对象

    def _send_reply(self, context: Context, reply: Reply):
        # 如果回复存在且回复类型不为空
        if reply and reply.type:
            # 触发事件: 在插件管理器中触发发送回复事件
            e_context = PluginManager().emit_event(
                EventContext(
                    Event.ON_SEND_REPLY,
                    {"channel": self, "context": context, "reply": reply},
                )
            )
            reply = e_context["reply"] # 更新回复对象，使用事件处理后的回复
            # 如果事件传播没有被停止，且回复有效
            if not e_context.is_pass() and reply and reply.type:
                # 打印日志，记录准备发送的回复和上下文信息
                logger.debug("[chat_channel] ready to send reply: {}, context: {}".format(reply, context))
                self._send(reply, context) # 调用发送方法实际发送回复
    # 进行 最多 3 次的重试，其中每次重试之间有逐步增加的等待时间。重试机制可以帮助应对一些临时的网络问题或者其他短期故障。
    def _send(self, reply: Reply, context: Context, retry_cnt=0):
        try:
            self.send(reply, context) # 调用子类特有的发送回复的方法
        except Exception as e:
            logger.error("[chat_channel] sendMsg error: {}".format(str(e)))
            if isinstance(e, NotImplementedError):
                return
            logger.exception(e)
            if retry_cnt < 2:
                time.sleep(3 + 3 * retry_cnt)
                self._send(reply, context, retry_cnt + 1)

    def _success_callback(self, session_id, **kwargs):  # 线程正常结束时的回调函数
        logger.debug("Worker return success, session_id = {}".format(session_id))

    def _fail_callback(self, session_id, exception, **kwargs):  # 线程异常结束时的回调函数
        logger.exception("Worker return exception: {}".format(exception))
    # 它会在线程池中的任务完成时被调用，并处理任务执行的结果。这个回调函数封装了两个主要的部分：成功回调 和 失败回调
    # func 是一个 闭包，因为它引用了外部函数 _thread_pool_callback 的局部变量（session_id 和 kwargs），并且这个内部函
    # 数（func）将在其外部作用域完成后依然可以访问这些变量。
    def _thread_pool_callback(self, session_id, **kwargs):
        # 这是内部定义的回调函数 func，它会在任务完成时被调用。它的参数 worker 是一个 Future 对象，表示任务的状态。Future
        # 对象可以用来检查任务的执行结果，比如是否抛出了异常，任务是否成功完成等。
        def func(worker: Future):
            try:
                # worker.exception() 是 Python 中 Future 对象的一种方法，用于检查并获取异步任务（或者
                # 说是线程/进程池中的任务）执行时是否抛出了异常。
                worker_exception = worker.exception()
                # orker.exception() 会检查任务是否抛出了异常。如果任务失败并抛出异常，exception() 会返回异常对象,
                # 否则返回 None。
                if worker_exception:
                    # 如果有异常，调用 self._fail_callback() 来处理失败的回调，传递 session_id、异常信息以及额外的 kwargs
                    self._fail_callback(session_id, exception=worker_exception, **kwargs)
                else:
                    # 如果任务没有异常（即返回None），则调用 self._success_callback() 来处理成功的回调，传递 session_id 和其他的 kwargs。
                    self._success_callback(session_id, **kwargs)
            except CancelledError as e:# 表示任务被取消时，会记录日志。
                logger.info("Worker cancelled, session_id = {}".format(session_id))
            except Exception as e:
                # 捕获其他异常并记录详细的错误日志。这样可以避免某些未捕获的错误导致系统崩溃。
                logger.exception("Worker raise exception: {}".format(e))
            with self.lock:
                # self.sessions 可能在多个线程之间共享访问，所以通过使用 self.lock 来保护对 self.sessions 的访问
                # self.sessions[session_id]返回context_queue, semaphore,[1]访问的是信号量
                self.sessions[session_id][1].release() # 释放信号量
        return func
    # 把消息放入自己所属的session对应的队列中
    def produce(self, context: Context):
        # 从context对象中提取session_id
        session_id = context["session_id"]
        # 获取锁，确保在访问共享资源时的线程安全
        with self.lock:
            # 检查session_id是否不在sessions字典中
            if session_id not in self.sessions:
                # 如果不在，初始化该session，包含一个新的Dequeue和一个有界信号量
                # 信号量控制此session的最大并发访问数，默认值为4
                self.sessions[session_id] = [
                    Dequeue(),
                    threading.BoundedSemaphore(conf().get("concurrency_in_session", 4)),
                ]
            # 检查context的类型是否为TEXT，并且内容是否以"#"开头
            if context.type == ContextType.TEXT and context.content.startswith("#"):
                # 如果是管理命令（以"#"开头），将其放到队列的最前面,[0]是获取队列,putleft放到前面
                # 这样确保管理命令优先处理
                self.sessions[session_id][0].putleft(context) 
            else:
                # 否则，将context放到队列的末尾进行正常处理
                self.sessions[session_id][0].put(context)
    # 一个会话（session）通常对应一个群聊或私聊。会话可以帮助管理和跟踪消息的状态、上下文和处理过程。以下是一些更详细的解释：
    # 私聊会话：每个私聊会话通常对应一个用户与机器人的对话。这种会话的 session_id 可以是用户的唯一标识符（如用户ID）。
    # 用途：用于跟踪该用户的对话上下文，确保机器人能够理解并回应用户连续的消息。
    # 群聊会话：每个群聊会话通常对应一个群组与机器人的对话。这种会话的 session_id 可以是群组的唯一标识符（如群组ID）。
    # 用途：用于跟踪该群组的对话上下文，确保机器人能够处理群聊中的多用户消息。
    # 任何一个线程进入了一个 with self.lock 块，其他线程不能进入任何其他 with self.lock 块，直到第一个线程释放锁。
    # 这确保了所有访问共享资源的代码块之间的互斥，从而防止数据竞争和不一致性。
    # 如果有多个chatchannel实例,就有多个线程调用,他们有可能同时处理同一个session_id下的消息队列,只要在其他线程释放锁后
    # 访问到session_ids
    def consume(self):
        # 这是一个无限循环，意味着这个线程会一直运行，持续从消息队列中取消息并处理。
        while True: 
            # 使用锁来确保对 self.sessions 字典的访问是线程安全的。
            with self.lock:  # 锁定 sessions 字典，获取所有 session_id 的列表
                session_ids = list(self.sessions.keys()) 
            # 遍历所有 session_id
            for session_id in session_ids: 
                # 再次锁定 sessions 字典，获取当前 session_id 对应的 context_queue 和 semaphore
                with self.lock: 
                    # 获取当前session_id对应的消息队列和信号量
                    context_queue, semaphore = self.sessions[session_id] 
                # 尝试获取信号量，并将信号量的计数减1。如果信号量的计数大于0，则获取成功，并将计数减1；如果信号量的计数已经是0，则
                # 获取失败，并立即返回 False，而不会阻塞等待。
                if semaphore.acquire(blocking=False): 
                    if not context_queue.empty():  # 如果队列不为空，从队列中取出一个 context
                        context = context_queue.get() 
                        logger.debug("[chat_channel] consume context: {}".format(context))
                        # 提交任务到线程池执行，处理 context
                        # handler_pool 是在类外面定义的全局线程池，最大线程数为8。
                        # ChatChannel 类的所有实例都共享这个全局线程池。
                        # 每个 ChatChannel 实例都会将任务提交到这个共享的线程池进行处理。
                        # 将 self._handle 方法提交给线程池 handler_pool 来执行，并返回一个 Future 对象。这个 
                        # Future 对象可以用来跟踪和管理这个异步任务。
                        future: Future = handler_pool.submit(self._handle, context)
                        # 注册回调函数，当任务完成时调用
                        future.add_done_callback(self._thread_pool_callback(session_id, context=context))
                        # 将 future 对象存储到 futures 字典中,session_id-->(future对象列表)
                        with self.lock:  
                            if session_id not in self.futures: 
                                self.futures[session_id] = []
                            self.futures[session_id].append(future)
                    # 如果有一个线程进入了if semaphore.acquire(blocking=False): 内,会消耗一个信号量,如果这时判断这个
                    # semaphore._initial_value == semaphore._value + 1成立,只能说明除了当前线程,没其他在用信号量的
                    # 这时前面的消息队列为空,前面线程使用的信号量已经被释放,这时可以断言当前session_id对应的任务完成,可以删除会话了
                    elif semaphore._initial_value == semaphore._value + 1: 
                        with self.lock:
                            # 找出session_id对应的异步任务中没完成的任务列表
                            self.futures[session_id] = [t for t in self.futures[session_id] if not t.done()]
                            # 断言当前session_id对应的没完成的任务为0
                            assert len(self.futures[session_id]) == 0, "thread pool error" 
                            # 因为当前session_id对应的消息队列里的消息已经全部处理完成，这时删除当前session_id对应的项
                            # 释放资源
                            del self.sessions[session_id]  
                    # 进入这个分支的条件是context_queue为空,并且不满足semaphore._initial_value == semaphore._value + 1
                    # 这个条件,说明有其他线程在做事情,这时就应该释放掉当前线程的信号量
                    else:
                        semaphore.release() 
             # 等待一段时间,进行下一轮消息的处理
            time.sleep(0.2) 

    # 取消session_id对应的所有任务，只能取消排队的消息和已提交线程池但未执行的任务
    def cancel_session(self, session_id):
        # 获取锁，确保在访问共享资源时的线程安全
        with self.lock:
            # 检查session_id是否在sessions字典中
            if session_id in self.sessions:
                # 取消所有与该session相关的future对象
                for future in self.futures[session_id]:
                    # cancel() 方法用于尝试取消该操作。如果调用成功并且操作被成功取消，则返回 True，否则返回 False。
                    future.cancel()
                # 获取该session中队列的大小（即消息数量）
                cnt = self.sessions[session_id][0].qsize()
                # 如果队列中还有消息，记录取消的消息数量和session_id
                if cnt > 0:
                    logger.info("Cancel {} messages in session {}".format(cnt, session_id))
                 # 将该session的队列重置为一个新的Dequeue对象
                self.sessions[session_id][0] = Dequeue()
    # 取消所有session_id对应的所有任务
    def cancel_all_session(self):
        with self.lock:
            for session_id in self.sessions:
                for future in self.futures[session_id]:
                    future.cancel()
                cnt = self.sessions[session_id][0].qsize()
                if cnt > 0:
                    logger.info("Cancel {} messages in session {}".format(cnt, session_id))
                self.sessions[session_id][0] = Dequeue()

# 检查content是否以前缀开始
def check_prefix(content, prefix_list):
    if not prefix_list:
        return None
    for prefix in prefix_list:
        if content.startswith(prefix):
            return prefix
    return None
# 函数的作用是检查 content 中是否包含 keyword_list 中的任何一个关键字。如果找到关键字则返回 True，否则返回 None。
def check_contain(content, keyword_list):
    if not keyword_list: # 如果 keyword_list 是空的，直接返回 None
        return None
    # 使用 str.find() 方法在 content 中查找关键字 ky。如果找到关键字（即返回值不等于 -1），则返回 True，
    # 表示 content 中包含该关键字。
    for ky in keyword_list:
        if content.find(ky) != -1:
            return True
    # 如果遍历完 keyword_list 后没有找到任何关键字，函数返回 None，表示 content 中不包含任何关键字。
    return None
