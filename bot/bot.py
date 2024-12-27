"""
Auto-replay chat robot abstract class
"""
from bridge.context import Context
from bridge.reply import Reply

# query 是用户发给机器人或系统的消息或问题。例如，用户可能会问：“今天天气如何？”
# context 提供了额外的上下文信息，帮助机器人理解当前查询的背景，从而生成更准确的回复。例如，context 可能包含之前
# 的对话内容，或者用户的历史交互等信息。
# Reply 是机器人的回复内容，它是机器人根据 query 和 context 生成的回应。
class Bot(object):
    # reply 方法需要被子类实现，生成具体的回复内容。因此，reply 方法的职责是根据 query 和 context 的输入，
    # 生成一个 Reply 对象作为输出。
    def reply(self, query, context: Context = None) -> Reply:
      
        raise NotImplementedError
