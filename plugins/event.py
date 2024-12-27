# encoding:utf-8
from enum import Enum
# Event 是一个枚举类型，表示一系列事件，每个事件都代表了系统中的一个状态或操作。
class Event(Enum):
    ON_RECEIVE_MESSAGE = 1  # 当系统接收到一条消息时触发的事件。
    """
    e_context = {  "channel": 消息channel, "context" : 本次消息的context}
    """

    ON_HANDLE_CONTEXT = 2  # 在处理消息内容之前触发的事件，可能会对消息内容做预处理。
    """
    e_context = {  "channel": 消息channel, "context" : 本次消息的context, "reply" : 目前的回复，初始为空  }
    """

    ON_DECORATE_REPLY = 3  # 当系统得到回复之后，准备进行装饰的事件，通常是在返回用户的回复之前做一些操作。
    """
    e_context = {  "channel": 消息channel, "context" : 本次消息的context, "reply" : 目前的回复 }
    """

    ON_SEND_REPLY = 4  # 在发送回复前触发的事件，用来进行最后的处理，可能会决定如何将回复返回给用户。
    """
    e_context = {  "channel": 消息channel, "context" : 本次消息的context, "reply" : 目前的回复 }
    """

    # AFTER_SEND_REPLY = 5    # 发送回复后

# 事件传播行为,事件传播链 的控制逻辑。具体来说，它们定义了事件在插件系统中如何传播，是否继续传递给下一个插件，或者终止传播。
# "默认的事件处理逻辑" 是chatchannel中的if not e_context.is_pass():之后的代码
class EventAction(Enum):
    CONTINUE = 1  # 事件未结束，继续交给下个插件处理，如果没有下个插件，则交付给默认的事件处理逻辑
    BREAK = 2  # 事件结束，不再给下个插件处理，交付给默认的事件处理逻辑
    BREAK_PASS = 3  # 事件结束，不再给下个插件处理，不交付给默认的事件处理逻辑

# EventContext 类用于存储每个事件的上下文数据以及事件的状态。每个事件都会关联一个 EventContext 对象，
# 这个对象包含事件相关的信息。
class EventContext:
    def __init__(self, event, econtext=dict()):
        self.event = event # 当前事件
        self.econtext = econtext  # 当前事件的上下文数据（一个字典）
        self.action = EventAction.CONTINUE # 事件行为

    def __getitem__(self, key):
        return self.econtext[key] # 允许通过 key 访问上下文数据

    def __setitem__(self, key, value):  # 允许通过 key 设置上下文数据
        self.econtext[key] = value

    def __delitem__(self, key):  # 允许通过 key 删除上下文数据
        del self.econtext[key]

    def is_pass(self):
        return self.action == EventAction.BREAK_PASS # 判断当前e_context的事件传播行为是否为 BREAK_PASS
    # 判断当前事件传播行为是否为 BREAK 或 BREAK_PASS
    def is_break(self):
        return self.action == EventAction.BREAK or self.action == EventAction.BREAK_PASS 