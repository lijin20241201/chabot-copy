# encoding:utf-8

import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from channel.chat_message import ChatMessage
from common.log import logger
from plugins import *
from config import conf

# desire_priority=-1 表示该插件的优先级较低，但并不一定是最小的。
# 插件系统的执行顺序是根据优先级的大小决定的，数值越大，优先级越高。
@plugins.register(
    name="Hello",
    desire_priority=-1,
    hidden=True,
    desc="A simple plugin that says hello",
    version="0.1",
    author="lanvent",
)
class Hello(Plugin):
    group_welc_prompt = "请你随机使用一种风格说一句问候语来欢迎新用户\"{nickname}\"加入群聊。"
    group_exit_prompt = "请你随机使用一种风格跟其他群用户说他违反规则\"{nickname}\"退出群聊。"
    patpat_prompt = "请你随机使用一种风格介绍你自己，并告诉用户输入#help可以查看帮助信息。"
    def __init__(self):
        super().__init__()
        try:
            self.config = super().load_config() # 加载当前插件配置
            if not self.config: # 如果不存在,就从模板加载
                self.config = self._load_config_template()
            # 获取群聊时的各个群的欢迎语
            self.group_welc_fixed_msg = self.config.get("group_welc_fixed_msg", {})
            # 群聊时机器人欢迎用户加入群聊
            self.group_welc_prompt = self.config.get("group_welc_prompt", self.group_welc_prompt)
            # 机器人像群内成员提示某用户退出群聊
            self.group_exit_prompt = self.config.get("group_exit_prompt", self.group_exit_prompt)
            # 机器人自我介绍
            self.patpat_prompt = self.config.get("patpat_prompt", self.patpat_prompt)
            logger.info("[Hello] inited")
            # 插件的handers字典,事件标记-->事件处理函数
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        except Exception as e:
            logger.error(f"[Hello]初始化异常：{e}")
            raise "[Hello] init failed, ignore "

    def on_handle_context(self, e_context: EventContext):
        # # 检查e_context消息类型，如果不符合预期的类型，则直接返回
        if e_context["context"].type not in [
            ContextType.TEXT,# 文本消息
            ContextType.JOIN_GROUP,# 加入群聊
            ContextType.PATPAT,# “拍了拍”动作。
            ContextType.EXIT_GROUP #退出群聊。
        ]:
            return
        msg: ChatMessage = e_context["context"]["msg"] # 获取消息对象
        # 获取群聊名称
        group_name = msg.from_user_nickname 
        # 处理用户加入群聊的情况
        if e_context["context"].type == ContextType.JOIN_GROUP:
            # 检查是否有全局或特定群聊的欢迎语
            if "group_welcome_msg" in conf() or group_name in self.group_welc_fixed_msg:
                reply = Reply() # 创建回复对象
                reply.type = ReplyType.TEXT # 回复类型为文本
                 # 使用特定群聊的欢迎语或全局欢迎语
                if group_name in self.group_welc_fixed_msg:
                    reply.content = self.group_welc_fixed_msg.get(group_name, "")
                else:
                    reply.content = conf().get("group_welcome_msg", "")
                # 将回复添加到e_context中
                e_context["reply"] = reply
                # 设置e_context的事件行为为BREAK_PASS,表示事件到此结束,不交给其他插件处理,也不交给默认的事件处理逻辑
                e_context.action = EventAction.BREAK_PASS 
                return
            # 如果没有特定欢迎语，则生成默认的欢迎信息
            e_context["context"].type = ContextType.TEXT
            e_context["context"].content = self.group_welc_prompt.format(nickname=msg.actual_user_nickname)
            # 当设置为 EventAction.BREAK 时，当前事件的处理流程会停止，后续的插件不会再处理该事件，控制权会被交给框架或默认
            # 的事件处理逻辑。
            e_context.action = EventAction.BREAK  
            # 给 context 添加一个属性，记录事件被打断的原因或标记，用于追踪和日志等目的。
            if not self.config or not self.config.get("use_character_desc"):
                e_context["context"]["generate_breaked_by"] = EventAction.BREAK
            return
         # 处理用户退出群聊的情况
        if e_context["context"].type == ContextType.EXIT_GROUP:
            # 如果配置项允许群聊退出时回复
            if conf().get("group_chat_exit_group"):
                e_context["context"].type = ContextType.TEXT
                e_context["context"].content = self.group_exit_prompt.format(nickname=msg.actual_user_nickname)
                e_context.action = EventAction.BREAK   # 结束事件，不再给下个插件处理,进入默认处理逻辑
                return
             # 不做任何回复，仅结束事件,不再给下个插件处理,进入默认处理逻辑
            e_context.action = EventAction.BREAK
            return
        # 处理“拍了拍”动作的情况 
        if e_context["context"].type == ContextType.PATPAT:
            e_context["context"].type = ContextType.TEXT
            e_context["context"].content = self.patpat_prompt # 回复“拍了拍”的提示内容
            e_context.action = EventAction.BREAK  # 结束事件，不再给下个插件处理,进入默认处理逻辑
            # 如果self.config为空或者use_character_desc为False,那么在事件上下文 e_context["context"] 中设置一个标记
            # generate_breaked_by，并将其值设置为 EventAction.BREAK。跳过基于角色描述的其他处理。
            # 如果 use_character_desc 为 True，说明系统启用了“角色描述”功能，可能会在生成回复时依据用户或机器人的角色描述生成更加个
            # 性化或具有情感色彩的回应。如果 use_character_desc 为 False，则禁用这一功能，意味着系统不会根据角色设定来定制回答，
            # 而是返回更加中性或默认的消息内容。
            if not self.config or not self.config.get("use_character_desc"):
                e_context["context"]["generate_breaked_by"] = EventAction.BREAK
            return
        # 获取消息内容
        content = e_context["context"].content
        logger.debug("[Hello] on_handle_context. content: %s" % content)
        # 如果消息内容为"Hello"，生成问候回复
        if content == "Hello":
            reply = Reply()
            reply.type = ReplyType.TEXT  # 回复类型为文本
            # 根据是否是群聊发送不同的问候
            if e_context["context"]["isgroup"]:
                reply.content = f"Hello, {msg.actual_user_nickname} from {msg.from_user_nickname}"
            else:
                reply.content = f"Hello, {msg.from_user_nickname}"
            e_context["reply"] = reply  # 添加回复到e_context
            # 设置e_context的事件传播行为为BREAK_PASS,事件结束，不再给下个插件处理，不交给默认的事件处理逻辑
            e_context.action = EventAction.BREAK_PASS  
        # 如果消息内容为"Hi"，生成简单的"Hi"回复
        if content == "Hi":
            reply = Reply()
            reply.type = ReplyType.TEXT
            reply.content = "Hi"  # 回复内容为"Hi"
            e_context["reply"] = reply
            # 事件结束，进入默认处理逻辑，一般会覆写reply,覆写reply 指的是后续的处理逻辑可以修改 e_context["reply"] 
            # 中的内容，替换掉之前设置的 reply。
            e_context.action = EventAction.BREAK  
        # 如果消息内容为"End"，将消息类型改为创建图片，并设置图片内容
        if content == "End":
            # 如果是文本消息"End"，将请求转换成"IMAGE_CREATE"，并将content设置为"The World"
            e_context["context"].type = ContextType.IMAGE_CREATE  # 修改消息类型为图片生成
            content = "The World"   # 设置图片生成的内容
            # 设置事件上下文的事件传播行为为CONTINUE,事件未结束，继续交给下个插件处理，如果没有下个插件，
            # 则交付给默认的事件处理逻辑
            e_context.action = EventAction.CONTINUE  
    # 帮助文本内容：help_text 变量中存储了一段字符串，它告诉用户两种输入命令及其预期的响应
    # 输入“Hello”，系统会回复用户的名字。输入“End”，系统会回复一张“世界的图片”。
    def get_help_text(self, **kwargs):
        help_text = "输入Hello，我会回复你的名字\n输入End，我会回复你世界的图片\n"
        return help_text
    # 加载插件配置,返回插件配置字典
    def _load_config_template(self):
        logger.debug("No Hello plugin config.json, use plugins/hello/config.json.template")
        try:
            plugin_config_path = os.path.join(self.path, "config.json.template")
            if os.path.exists(plugin_config_path):
                with open(plugin_config_path, "r", encoding="utf-8") as f:
                    plugin_conf = json.load(f)
                    return plugin_conf
        except Exception as e:
            logger.exception(e)