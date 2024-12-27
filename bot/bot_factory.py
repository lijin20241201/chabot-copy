from common import const
# 根据bot_type创建不同类型的对话机器人实例
def create_bot(bot_type):
    if bot_type == const.BAIDU:
        # 创建百度文心千帆对话接口的机器人实例
        # 替换Baidu Unit为Baidu文心千帆对话接口
        # from bot.baidu.baidu_unit_bot import BaiduUnitBot
        # return BaiduUnitBot()
        from bot.baidu.baidu_wenxin import BaiduWenxinBot
        return BaiduWenxinBot()

    elif bot_type == const.CHATGPT:
        # 创建基于ChatGPT网页端web接口的机器人实例
        from bot.chatgpt.chat_gpt_bot import ChatGPTBot
        return ChatGPTBot()

    elif bot_type == const.OPEN_AI:
        # # 创建使用OpenAI官方对话模型API的机器人实例
        from bot.openai.open_ai_bot import OpenAIBot
        return OpenAIBot()

    elif bot_type == const.CHATGPTONAZURE:
        # Azure chatgpt service https://azure.microsoft.com/en-in/products/cognitive-services/openai-service/
        # 创建基于Azure提供的ChatGPT服务的机器人实例
        from bot.chatgpt.chat_gpt_bot import AzureChatGPTBot
        return AzureChatGPTBot()

    elif bot_type == const.XUNFEI:
        # 创建讯飞星火对话机器人的实例
        from bot.xunfei.xunfei_spark_bot import XunFeiBot
        return XunFeiBot()

    elif bot_type == const.LINKAI:
        # 创建LinkAI对话机器人的实例
        from bot.linkai.link_ai_bot import LinkAIBot
        return LinkAIBot()

    elif bot_type == const.CLAUDEAI:
        # 创建Claude AI对话机器人的实例
        from bot.claude.claude_ai_bot import ClaudeAIBot
        return ClaudeAIBot()
    elif bot_type == const.CLAUDEAPI:
        # 创建使用Claude API的对话机器人实例
        from bot.claudeapi.claude_api_bot import ClaudeAPIBot
        return ClaudeAPIBot()
    elif bot_type == const.QWEN:
        # 创建阿里云Qwen对话机器人的实例
        from bot.ali.ali_qwen_bot import AliQwenBot
        return AliQwenBot()
    elif bot_type == const.QWEN_DASHSCOPE:
        # 创建基于Dashscope平台的Qwen对话机器人实例
        from bot.dashscope.dashscope_bot import DashscopeBot
        return DashscopeBot()
    elif bot_type == const.GEMINI:
        # 创建Google Gemini对话机器人的实例
        from bot.gemini.google_gemini_bot import GoogleGeminiBot
        return GoogleGeminiBot()

    elif bot_type == const.ZHIPU_AI:
        # 创建智谱AI对话机器人的实例
        from bot.zhipuai.zhipuai_bot import ZHIPUAIBot
        return ZHIPUAIBot()

    elif bot_type == const.MOONSHOT:
        # 创建Moonshot对话机器人的实例
        from bot.moonshot.moonshot_bot import MoonshotBot
        return MoonshotBot()
    
    elif bot_type == const.MiniMax:
        # 创建MiniMax对话机器人的实例
        from bot.minimax.minimax_bot import MinimaxBot
        return MinimaxBot()
    # 如果bot_type不匹配任何已知类型，则抛出运行时错误
    raise RuntimeError
