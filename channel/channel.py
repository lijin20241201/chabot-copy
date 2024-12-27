from bridge.bridge import Bridge
from bridge.context import Context
from bridge.reply import *
# 这段代码定义了一个名为 Channel 的基类，它为所有具体通道（如微信、终端、Web 等）提供了一个通用的接口。通过继承这个基类并实现其
# 抽象方法，不同的通道可以共享相同的接口和行为，同时保持各自的特异性。
class Channel(object):
    # 类变量是属于类本身而不是类的实例（对象）。它们存储的是该类的共享状态，即所有实例共享相同的类变量。
    channel_type = "" # 用于存储通道类型名称。子类应设置此属性以标识具体的通道类型。
    # 类变量，包含一个列表，列出不支持的回复类型（例如语音和图像）。这可以帮助子类在发送消息时进行检查，避免发送不受支持的消息类型。
    # 对于 NOT_SUPPORT_REPLYTYPE 属性，如果它是在父类中定义的一个类属性（class attribute），那么子类可以通过重新定义这个属性来改变它的值。
    NOT_SUPPORT_REPLYTYPE = [ReplyType.VOICE, ReplyType.IMAGE]
    # 抽象方法 这些方法需要在子类中实现，因为它们是每个通道特有的行为：
    # 初始化通道。每个子类都需要根据自身特点实现这个方法，例如建立连接、加载配置等。
    def startup(self):
        raise NotImplementedError
    # 处理接收到的文本消息。子类应该根据具体需求解析和处理消息，并可能调用其他方法来生成回复
    def handle_text(self, msg):
        raise NotImplementedError # 未实现错误
    # 统一的发送函数，每个Channel自行实现，根据reply的type字段发送不同类型的回复
    def send(self, reply: Reply, context: Context):
        raise NotImplementedError
    # 公共方法  这些方法提供了通用的功能，可以在子类中直接使用或进一步扩展：
    # 构建回复内容。调用了 Bridge 类的方法来获取回复内容，适用于大多数情况下的文本回复生成。
    def build_reply_content(self, query, context: Context = None) -> Reply:
        return Bridge().fetch_reply_content(query, context)
    # 将语音文件转换为文本。同样调用了 Bridge 类的方法，适用于处理语音输入。
    def build_voice_to_text(self, voice_file) -> Reply:
        return Bridge().fetch_voice_to_text(voice_file)
    # 将文本转换为语音。也调用了 Bridge 类的方法，适用于生成语音回复。
    def build_text_to_voice(self, text) -> Reply:
        return Bridge().fetch_text_to_voice(text)
