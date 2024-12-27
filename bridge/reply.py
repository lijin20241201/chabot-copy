# encoding:utf-8

from enum import Enum
# ReplyType 这个枚举类定义了不同类型的机器人回复。
class ReplyType(Enum):
    TEXT = 1  # 代表普通的文本消息。
    VOICE = 2  # 代表音频文件的回复。
    IMAGE = 3  # 代表图片文件的回复。
    IMAGE_URL = 4  #  代表通过图片 URL 的回复。
    VIDEO_URL = 5  # 代表视频 URL 的回复。
    FILE = 6  # 代表文件的回复。
    CARD = 7  # 代表微信名片的回复（这个类型通常只在一些特定平台如 ntchat 中支持）
    INVITE_ROOM = 8  # 代表邀请好友进群的消息。
    INFO = 9 # 日志
    ERROR = 10 # 代表错误回复。
    TEXT_ = 11  # 强制文本
    VIDEO = 12
    MINIAPP = 13  # 代表小程序类型的回复。
    def __str__(self):
        return self.name
# Reply 类封装了机器人的回复内容。它包含两个主要属性
# type: 使用 ReplyType 枚举类型，表示回复的类型（例如文本、图片、音频等）。
# content: 回复的具体内容，这个内容根据类型可能是字符串、文件、图片 URL 等。
class Reply:
    def __init__(self, type: ReplyType = None, content=None):
        self.type = type
        self.content = content

    def __str__(self):
        return "Reply(type={}, content={})".format(self.type, self.content)
