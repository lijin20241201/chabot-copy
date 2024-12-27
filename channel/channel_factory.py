from common import const
from .channel import Channel
# 创建通道实例
def create_channel(channel_type) -> Channel:
    # 创建一个默认的 Channel 实例 ch。这通常是为了确保在所有条件下都有一个有效的通道对象，即使没有匹配到具体的通道类型。
    ch = Channel()
    # 根据通道类型创建具体通道实例
    if channel_type == "wx": # 这个通道可能用于通过微信官方 API 进行交互。
        from channel.wechat.wechat_channel import WechatChannel
        ch = WechatChannel()
    elif channel_type == "wxy": # 这个通道使用 Wechaty 库来与微信平台进行交互，提供了更高层次的抽象和额外功能。
        from channel.wechat.wechaty_channel import WechatyChannel
        ch = WechatyChannel()
    elif channel_type == "terminal": # 这个通道用于通过命令行界面（CLI）与用户进行交互。
        from channel.terminal.terminal_channel import TerminalChannel
        ch = TerminalChannel()
    elif channel_type == 'web': # 这个通道可能用于通过 HTTP/HTTPS 协议与 Web 客户端进行交互。
        from channel.web.web_channel import WebChannel
        ch = WebChannel()
    # 微信公众号通道 (wechatmp 和 wechatmp_service)
    elif channel_type == "wechatmp":
        from channel.wechatmp.wechatmp_channel import WechatMPChannel
        # passive_reply 参数控制是否被动回复消息，适用于不同场景下的微信公众号交互。
        ch = WechatMPChannel(passive_reply=True)
    elif channel_type == "wechatmp_service":
        from channel.wechatmp.wechatmp_channel import WechatMPChannel
        ch = WechatMPChannel(passive_reply=False)
    elif channel_type == "wechatcom_app":
        from channel.wechatcom.wechatcomapp_channel import WechatComAppChannel
        ch = WechatComAppChannel()
    # 企业微信通道 (wework)
    elif channel_type == "wework":
        from channel.wework.wework_channel import WeworkChannel
        ch = WeworkChannel() # 这个通道用于与企业微信平台进行交互。
    # 飞书通道 (feishu)
    elif channel_type == const.FEISHU:
        from channel.feishu.feishu_channel import FeiShuChanel
        ch = FeiShuChanel() # 这个通道用于与飞书平台进行交互。
    # 钉钉通道 (dingtalk)
    elif channel_type == const.DINGTALK:
        from channel.dingtalk.dingtalk_channel import DingTalkChanel
        ch = DingTalkChanel() # 这个通道用于与钉钉平台进行交互。
    else: # 如果 channel_type 不匹配任何已知类型，则抛出 RuntimeError 异常
        raise RuntimeError
    ch.channel_type = channel_type
    return ch
