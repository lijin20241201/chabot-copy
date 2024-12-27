# encoding:utf-8
import json
import os
import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from plugins import *
from .lib.WordsSearch import WordsSearch

# plugins.register调用的是plugins中__init__下的register,是个装饰器
# 用于把插件放入PluginManager的self.plugins中
# hidden=True：插件不会出现在用户界面中，通常用于隐藏插件或开发时的插件。
# hidden=False：插件会出现在用户界面中，供用户选择和启用。
@plugins.register(
    name="Banwords", 
    desire_priority=100,
    hidden=True,
    desc="判断消息中是否有敏感词、决定是否回复。",
    version="1.0",
    author="lanvent",
)
class Banwords(Plugin):
    def __init__(self):
        super().__init__() # 调用父类的构造函数，初始化父类的属性和方法
        try:
            # 返回插件配置字典,并且写入全局配置字典
            conf = super().load_config() 
            curdir = os.path.dirname(__file__) # 获取当前脚本所在目录
            # 如果配置不存在,就写默认conf到文件中
            if not conf: 
                config_path = os.path.join(curdir, "config.json")
                if not os.path.exists(config_path):
                    conf = {"action": "ignore"} # 默认配置内容
                    with open(config_path, "w") as f:
                        json.dump(conf, f, indent=4)  # 将默认配置保存到 config.json 文件中
            
            self.searchr = WordsSearch() # 初始化一个 WordsSearch 对象，可能用于关键词搜索
            self.action = conf["action"] # 从配置中读取 action 字段，用于后续操作
            banwords_path = os.path.join(curdir, "banwords.txt") # 获取禁止词列表的文件路径
            with open(banwords_path, "r", encoding="utf-8") as f:  # 以 UTF-8 编码打开 banwords.txt 文件
                words = [] # 创建一个空列表，用于存储禁止的词
                for line in f:
                    word = line.strip()
                    if word: # 如果该行不为空（避免空行）
                        words.append(word)
            self.searchr.SetKeywords(words) # 将禁止词列表传递给 WordsSearch 对象
            # 这个函数会处理接收到的消息内容，特别是 content 消息。消息内容中的禁止词很可能会被 replace 操作替换掉。
            # 因此，action: "replace" 表示对接收到的内容进行词汇替换，而不是对回复进行修改。
            # 接收到的 content 消息：会根据 action: "replace" 进行禁止词替换。
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context  # 注册事件处理函数 ON_HANDLE_CONTEXT
            # self.handlers[Event.ON_DECORATE_REPLY] = self.on_decorate_reply 事件处理函数用于处理 回复内容。
            # 这个处理仅在 reply_filter: true 时启用，意味着如果有回复消息，on_decorate_reply 会被调用。
            if conf.get("reply_filter", True): # 如果配置中开启了回复过滤（默认是开启的）
                # 回复消息：虽然启用了 reply_filter，但是由于 reply_action: "ignore"，回复内容不会被修改，忽略所有操作。
                self.handlers[Event.ON_DECORATE_REPLY] = self.on_decorate_reply  # 注册事件处理函数 ON_DECORATE_REPLY
                self.reply_action = conf.get("reply_action", "ignore") # 从配置中读取 reply_action，默认值是 "ignore"
            logger.info("[Banwords] inited")  # 输出日志，表示 Banwords 插件初始化成功
        except Exception as e: # 捕获所有异常
            logger.warn("[Banwords] init failed, ignore or see https://github.com/zhayujie/chatgpt-on-wechat/tree/master/plugins/banwords .")
            raise e  # 抛出异常，以便外部捕获

    def on_handle_context(self, e_context: EventContext):
        # 检查事件上下文中的消息类型，只有 TEXT 或 IMAGE_CREATE 类型的消息才会继续处理
        if e_context["context"].type not in [
            ContextType.TEXT, # 文本消息
            ContextType.IMAGE_CREATE, # 图片创建消息
        ]:
            return # 如果消息类型不匹配，直接返回，不做任何处理
        
        content = e_context["context"].content # 获取消息内容
        logger.debug("[Banwords] on_handle_context. content: %s" % content) # 打印消息内容到日志
         # 如果设置的动作是“ignore”（忽略敏感词），进行敏感词检查
        # 如果消息中包含敏感词并且设置为“忽略”，就不需要执行其他的处理（如回复或替换敏感词）。
        # 简化流程：直接退出方法，意味着不需要处理任何内容，也不需要生成任何回复或执行后续动作。这在某些情况下是非常有
        # 用的，特别是当我们希望某些消息直接被忽略或屏蔽时。
        if self.action == "ignore":
            f = self.searchr.FindFirst(content)  # 在消息内容中查找第一个敏感词
            if f:
                logger.info("[Banwords] %s in message" % f["Keyword"]) # 如果找到敏感词，记录日志
                e_context.action = EventAction.BREAK_PASS  # 跳过后续处理，直接跳到下一个事件
                return # 退出当前方法，避免后续处理
        # 如果设置的动作是“replace”（替换敏感词），进行敏感词替换
        # 替换敏感词时，系统会返回一条告知用户替换了敏感词的消息，并结束当前事件的处理。
        # 通过 BREAK_PASS，事件的传播被终止，系统跳过默认的后续处理逻辑，直接进入下一个事件的处理阶段。
        elif self.action == "replace":
            if self.searchr.ContainsAny(content):  # 如果消息内容包含任意敏感词
                # 用替换后的消息创建一个新的回复，告知用户已替换敏感词
                reply = Reply(ReplyType.INFO, "发言中包含敏感词，请重试: \n" + self.searchr.Replace(content))
                e_context["reply"] = reply # 将替换后的回复内容添加到事件上下文中
                e_context.action = EventAction.BREAK_PASS  # 跳过后续处理，直接跳到下一个事件
                return # 结束当前方法，避免继续处理

    def on_decorate_reply(self, e_context: EventContext):
        # 只处理文本类型的回复
        if e_context["reply"].type not in [ReplyType.TEXT]: # 只有文本类型的回复才继续处理
            return  # 如果不是文本类型的回复，直接返回，不做任何处理
        reply = e_context["reply"] # 获取当前回复对象
        content = reply.content # 获取回复的内容
         # 如果设置的回复动作是“ignore”（忽略敏感词），进行敏感词检查
        # 当设置回复行为为“忽略”时，如果回复内容中包含敏感词，系统会停止处理并不发送任何回复。
        # 通过将 e_context["reply"] 设置为 None，并使用 BREAK_PASS 跳过后续处理，确保不产生任何回应。
        if self.reply_action == "ignore":
            f = self.searchr.FindFirst(content) # 在回复内容中查找第一个敏感词
            if f:
                logger.info("[Banwords] %s in reply" % f["Keyword"]) # 如果找到敏感词，记录日志
                e_context["reply"] = None # 将回复内容设为 None，表示不返回回复
                e_context.action = EventAction.BREAK_PASS  # 跳过后续处理，直接跳到下一个事件
                return  # 结束当前方法，避免继续处理
         # 如果设置的回复动作是“replace”（替换敏感词），进行敏感词替换
        # 替换敏感词时，机器人会生成一个新回复，告知用户已替换敏感词。通过 EventAction.CONTINUE，事件会继续传播，交给下
        # 一个插件或者后续的处理流程。这样，系统可以进行多阶段的处理，不会因为替换敏感词而阻塞后续的操作。
        elif self.reply_action == "replace":
            if self.searchr.ContainsAny(content):  # 如果回复内容包含任意敏感词
                 # 创建一个新的回复，告知用户已替换回复中的敏感词
                reply = Reply(ReplyType.INFO, "已替换回复中的敏感词: \n" + self.searchr.Replace(content))
                e_context["reply"] = reply # 将替换后的回复内容添加到事件上下文中
                e_context.action = EventAction.CONTINUE  # 继续执行后续处理
                return  # 结束当前方法，避免继续处理

    def get_help_text(self, **kwargs):
        return "过滤消息中的敏感词。"
