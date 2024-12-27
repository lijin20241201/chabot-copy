# 机器人类型
OPEN_AI = "openAI" # 标识OpenAI的ChatGPT模型。
CHATGPT = "chatGPT"
BAIDU = "baidu"  # 百度文心一言模型
XUNFEI = "xunfei" # 科大讯飞的语音和语言处理服务。
CHATGPTONAZURE = "chatGPTOnAzure" # 标识部署在Azure云平台上的ChatGPT模型。
LINKAI = "linkai" # 标识LinkAI提供的语言模型或服务。
CLAUDEAI = "claude"  # 标识Anthropic公司的Claude模型，使用cookie的历史模型。
CLAUDEAPI= "claudeAPI"  # 标识通过官方API调用的Claude模型。
QWEN = "qwen"  # 标识阿里云的通义千问（旧版）模型。
QWEN_DASHSCOPE = "dashscope"  # 通义新版sdk和api key,标识阿里云通义千问的新版SDK和API Key。


GEMINI = "gemini"  # gemini-1.0-pro 标识Gemini-1.0-pro模型。
ZHIPU_AI = "glm-4" # 标识智谱AI的GLM-4模型。
MOONSHOT = "moonshot" # 标识Moonshot模型或服务。
MiniMax = "minimax" # 标识MiniMax模型或服务。 资源受限环境下的自然语言处理任务。
# model
CLAUDE3 = "claude-3-opus-20240229" # 标识Anthropic公司的Claude 3模型，发布日期为2024年2月29日。
GPT35 = "gpt-3.5-turbo" # 标识OpenAI的GPT-3.5 Turbo模型。
GPT35_0125 = "gpt-3.5-turbo-0125" # 标识GPT-3.5 Turbo模型的一个特定版本
GPT35_1106 = "gpt-3.5-turbo-1106" # 标识GPT-3.5 Turbo模型的一个特定版本

GPT_4o = "gpt-4o" # 标识OpenAI的GPT-4优化版模型。
GPT_4O_0806 = "gpt-4o-2024-08-06" # 标识GPT-4优化版模型的一个特定版本
GPT4_TURBO = "gpt-4-turbo" # 标识OpenAI的GPT-4 Turbo模型。
GPT4_TURBO_PREVIEW = "gpt-4-turbo-preview" # 标识GPT-4 Turbo模型的预览版本。
GPT4_TURBO_04_09 = "gpt-4-turbo-2024-04-09" # 标识GPT-4 Turbo模型的一个特定版本
GPT4_TURBO_01_25 = "gpt-4-0125-preview" # 标识GPT-4 Turbo模型的预览版本
GPT4_TURBO_11_06 = "gpt-4-1106-preview" # 标识GPT-4 Turbo模型的预览版本
GPT4_VISION_PREVIEW = "gpt-4-vision-preview" # 标识GPT-4 Vision模型的预览版本。

GPT4 = "gpt-4" # 标识OpenAI的GPT-4模型。
GPT_4o_MINI = "gpt-4o-mini" # 标识GPT-4优化版的小型化模型。
GPT4_32k = "gpt-4-32k" # 标识具有32K上下文窗口的GPT-4模型。
GPT4_06_13 = "gpt-4-0613" # 标识GPT-4模型的一个特定版本
GPT4_32k_06_13 = "gpt-4-32k-0613" # 标识具有32K上下文窗口的GPT-4模型的一个特定版本

O1 = "o1-preview"
O1_MINI = "o1-mini"

WHISPER_1 = "whisper-1"
TTS_1 = "tts-1"
TTS_1_HD = "tts-1-hd"

WEN_XIN = "wenxin"
WEN_XIN_4 = "wenxin-4"

QWEN_TURBO = "qwen-turbo"
QWEN_PLUS = "qwen-plus"
QWEN_MAX = "qwen-max"

LINKAI_35 = "linkai-3.5"
LINKAI_4_TURBO = "linkai-4-turbo"
LINKAI_4o = "linkai-4o"

GEMINI_PRO = "gemini-1.0-pro"
GEMINI_15_flash = "gemini-1.5-flash"
GEMINI_15_PRO = "gemini-1.5-pro"
GEMINI_20_flash_exp = "gemini-2.0-flash-exp"


GLM_4 = "glm-4"
GLM_4_PLUS = "glm-4-plus"
GLM_4_flash = "glm-4-flash"
GLM_4_LONG = "glm-4-long"
GLM_4_ALLTOOLS = "glm-4-alltools"
GLM_4_0520 = "glm-4-0520"
GLM_4_AIR = "glm-4-air"
GLM_4_AIRX = "glm-4-airx"


CLAUDE_3_OPUS = "claude-3-opus-latest"
CLAUDE_3_OPUS_0229 = "claude-3-opus-20240229"

CLAUDE_35_SONNET = "claude-3-5-sonnet-latest"  # 带 latest 标签的模型名称，会不断更新指向最新发布的模型
CLAUDE_35_SONNET_1022 = "claude-3-5-sonnet-20241022"  # 带具体日期的模型名称，会固定为该日期发布的模型
CLAUDE_35_SONNET_0620 = "claude-3-5-sonnet-20240620"
CLAUDE_3_SONNET = "claude-3-sonnet-20240229"

CLAUDE_3_HAIKU = "claude-3-haiku-20240307"

MODEL_LIST = [
              GPT35, GPT35_0125, GPT35_1106, "gpt-3.5-turbo-16k",
              O1, O1_MINI, GPT_4o, GPT_4O_0806, GPT_4o_MINI, GPT4_TURBO, GPT4_TURBO_PREVIEW, GPT4_TURBO_01_25, GPT4_TURBO_11_06, GPT4, GPT4_32k, GPT4_06_13, GPT4_32k_06_13,
              WEN_XIN, WEN_XIN_4,
              XUNFEI,
              ZHIPU_AI, GLM_4, GLM_4_PLUS, GLM_4_flash, GLM_4_LONG, GLM_4_ALLTOOLS, GLM_4_0520, GLM_4_AIR, GLM_4_AIRX,
              MOONSHOT, MiniMax,
              GEMINI, GEMINI_PRO, GEMINI_15_flash, GEMINI_15_PRO,GEMINI_20_flash_exp,
              CLAUDE_3_OPUS, CLAUDE_3_OPUS_0229, CLAUDE_35_SONNET, CLAUDE_35_SONNET_1022, CLAUDE_35_SONNET_0620, CLAUDE_3_SONNET, CLAUDE_3_HAIKU, "claude", "claude-3-haiku", "claude-3-sonnet", "claude-3-opus", "claude-3.5-sonnet",
              "moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k",
              QWEN, QWEN_TURBO, QWEN_PLUS, QWEN_MAX,
              LINKAI_35, LINKAI_4_TURBO, LINKAI_4o
            ]

# channel
FEISHU = "feishu" # 标识飞书（Feishu）消息通道。
DINGTALK = "dingtalk" # 标识钉钉（DingTalk）消息通道。
