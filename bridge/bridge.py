from bot.bot_factory import create_bot
from .context import Context
from .reply import Reply
from common import const
from common.log import logger
from common.singleton import singleton
from config import conf
from translate.factory import create_translator
from voice.factory import create_voice
# 这个类在聊天机器人应用中通常被称为 "桥接器"（Bridge）。它的作用是作为不同模型（如聊天、语音转文本、文本转语音、翻译等）的统一
# 接口，通过配置动态选择不同的模型类型，确保系统能够灵活地切换和使用不同的功能和服务。
# 在设计中，这个类利用了 单例模式（@singleton），确保系统中只有一个实例，避免重复创建模型实例，减少资源浪费，并通过配置来灵活选择和管理模型。
@singleton
class Bridge(object):
    def __init__(self):
        # self.btype 是一个字典，用来存储不同任务（如聊天、语音转文本、文本转语音、翻译）所对应的模型类型。
        self.btype = {
            "chat": const.CHATGPT,# 聊天
            "voice_to_text": conf().get("voice_to_text", "openai"), # 语音转文本
            "text_to_voice": conf().get("text_to_voice", "google"), # 文本转语音
            "translate": conf().get("translate", "baidu"), # 翻译
        }
        # bot_type 从配置中读取，如果存在，则将 self.btype["chat"] 设置为配置中的 bot_type，否则根据下面的条件进行模型选择。
        bot_type = conf().get("bot_type")
        if bot_type:
            self.btype["chat"] = bot_type
        else:
            # model_type 从配置中获取模型类型，如果没有配置，则使用默认的 const.GPT35。
            model_type = conf().get("model") or const.GPT35
            # 如果 model_type 是 text-davinci-003，则将 self.btype["chat"] 设置为 const.OPEN_AI，表示使用 OpenAI 的 Davinci 模型。
            if model_type in ["text-davinci-003"]:
                self.btype["chat"] = const.OPEN_AI
            # 如果配置中指定了 use_azure_chatgpt 为 True，则将聊天模型改为使用 Azure 上的 ChatGPT。
            if conf().get("use_azure_chatgpt", False):
                self.btype["chat"] = const.CHATGPTONAZURE
            # 如果 model_type 是 wenxin 或 wenxin-4，则选择百度的 BAIDU 模型。
            if model_type in ["wenxin", "wenxin-4"]:
                self.btype["chat"] = const.BAIDU
            # 如果 model_type 是 xunfei，则选择科大讯飞的 XUNFEI 模型。
            if model_type in ["xunfei"]:
                self.btype["chat"] = const.XUNFEI
            # 如果 model_type 是 const.QWEN，则选择 QWEN旧版模型。
            if model_type in [const.QWEN]:
                self.btype["chat"] = const.QWEN
            # 如果 model_type 是 QWEN_TURBO、QWEN_PLUS 或 QWEN_MAX，则选择 QWEN_DASHSCOPE 模型。
            if model_type in [const.QWEN_TURBO, const.QWEN_PLUS, const.QWEN_MAX]:
                self.btype["chat"] = const.QWEN_DASHSCOPE
            # 如果 model_type 以 "gemini" 开头，则选择 GEMINI 模型。
            if model_type and model_type.startswith("gemini"):
                self.btype["chat"] = const.GEMINI
            # 如果 model_type 以 "glm" 开头，则选择 ZHIPU_AI 模型。
            if model_type and model_type.startswith("glm"):
                self.btype["chat"] = const.ZHIPU_AI
            # 如果 model_type 以 "claude-3" 开头，则选择 CLAUDEAPI 模型。
            if model_type and model_type.startswith("claude-3"):
                self.btype["chat"] = const.CLAUDEAPI
            # 如果 model_type 是 claude，则选择 CLAUDEAI 模型。
            if model_type in ["claude"]:
                self.btype["chat"] = const.CLAUDEAI
            # 如果 model_type 是 Moonshot 系列模型，则选择 MOONSHOT 模型。
            if model_type in [const.MOONSHOT, "moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]:
                self.btype["chat"] = const.MOONSHOT
            if model_type in ["abab6.5-chat"]:
                self.btype["chat"] = const.MiniMax
            # 如果配置中启用了 use_linkai 且提供了 linkai_api_key，则选择 LinkAI 模型。
            if conf().get("use_linkai") and conf().get("linkai_api_key"):
                self.btype["chat"] = const.LINKAI
                if not conf().get("voice_to_text") or conf().get("voice_to_text") in ["openai"]:
                    self.btype["voice_to_text"] = const.LINKAI
                # 当 text_to_voice 未指定，或者它指定的是某些特定的值（如 openai、const.TTS_1、const.TTS_1_HD），
                # 则将 text_to_voice 设为 const.LINKAI。
                if not conf().get("text_to_voice") or conf().get("text_to_voice") in ["openai", const.TTS_1, const.TTS_1_HD]:
                    self.btype["text_to_voice"] = const.LINKAI
        # 初始化两个空字典 self.bots 和 self.chat_bots，用来存储各类机器人的实例。
        self.bots = {}
        self.chat_bots = {}
    # get_bot 方法根据 typename 获取相应的机器人实例。
    def get_bot(self, typename):
        # 如果 self.bots 字典中没有该机器人实例，则创建一个新的。
        if self.bots.get(typename) is None:
            # 根据任务类型（如 text_to_voice、voice_to_text、chat、translate）调用不同的创建方法（如 create_voice、create_bot、
            # create_translator）来创建机器人实例。
            logger.info("create bot {} for {}".format(self.btype[typename], typename))
            
            if typename == "text_to_voice": # 文本转语音
                self.bots[typename] = create_voice(self.btype[typename])
            elif typename == "voice_to_text": # 语音转文本
                self.bots[typename] = create_voice(self.btype[typename]) 
            elif typename == "chat":
                self.bots[typename] = create_bot(self.btype[typename]) # 聊天型
            elif typename == "translate": # 翻译
                self.bots[typename] = create_translator(self.btype[typename])
        return self.bots[typename]
   #  get_bot_type 方法返回 typename 对应的机器人类型（即 self.btype[typename] 的值）。
    def get_bot_type(self, typename):
        return self.btype[typename]
    # 处理回复内容、语音转文本、文本转语音和翻译
    # fetch_reply_content 方法调用聊天机器人来获取回复内容。
    def fetch_reply_content(self, query, context: Context) -> Reply:
        return self.get_bot("chat").reply(query, context)
    # fetch_voice_to_text 方法调用语音转文本机器人将语音文件转换为文本。
    def fetch_voice_to_text(self, voiceFile) -> Reply:
        return self.get_bot("voice_to_text").voiceToText(voiceFile)
    # fetch_text_to_voice 方法调用文本转语音机器人将文本转换为语音。
    def fetch_text_to_voice(self, text) -> Reply:
        return self.get_bot("text_to_voice").textToVoice(text)
    # fetch_translate 方法调用翻译机器人将文本从 from_lang 语言翻译为 to_lang 语言。
    def fetch_translate(self, text, from_lang="", to_lang="en") -> Reply:
        return self.get_bot("translate").translate(text, from_lang, to_lang)
    # 查找聊天机器人实例
    def find_chat_bot(self, bot_type: str):
        # 如果chat_bots里没有对应的模型,就构建一个，之后返回
        if self.chat_bots.get(bot_type) is None:
            self.chat_bots[bot_type] = create_bot(bot_type)
        return self.chat_bots.get(bot_type)
    # 重置配置：调用 __init__ 方法会根据配置文件（如通过 conf() 获取的配置）重新设置机器人的类型（例如 chat、voice_to_text 等）。
    # 刷新机器人实例：当配置被更新或改变时，reset_bot 方法会清空旧的配置并重新加载，确保使用最新的配置来创建机器人实例。
    # 使用场景
    # 如果在系统运行过程中，某些配置（例如使用的聊天机器人类型）发生了变化，调用 reset_bot 可以重新加载这些配置并应用到相应的机器人任务中。
    # 这对于需要根据动态配置或外部输入改变机器人的情况特别有用。
    def reset_bot(self):
        self.__init__()
