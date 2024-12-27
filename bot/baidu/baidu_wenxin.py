# encoding:utf-8

import requests
import json
from common import const
from bot.bot import Bot
from bot.session_manager import SessionManager
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf
from bot.baidu.baidu_wenxin_session import BaiduWenxinSession
# API Key：标识应用身份，类似用户名，用于识别请求的来源。
# Secret Key：用于加密签名和验证请求的真实性，类似密码，需保密。
# 这两者通常是配合使用的：API_KEY 告诉服务你是谁，SECRET_KEY 用于验证你是否有权限调用接口，并确保请求的安全性。
BAIDU_API_KEY = conf().get("baidu_wenxin_api_key")
BAIDU_SECRET_KEY = conf().get("baidu_wenxin_secret_key")
# 使用百度的 Wenxin（文心）模型来生成对话回复。该类处理文本和图像生成的请求，并支持记忆清除功能。
class BaiduWenxinBot(Bot):
    def __init__(self):
        super().__init__() # 调用父类 Bot 的构造方法，确保基类的一些初始化过程被执行。
        # 从配置中获取 wenxin_model 和 prompt_enabled 配置项
        wenxin_model = conf().get("baidu_wenxin_model") # wenxin_model 是配置的百度文心模型的名称。
        # prompt_enabled 是一个布尔值，指示是否启用自定义提示（prompt）
        self.prompt_enabled = conf().get("baidu_wenxin_prompt_enabled")
        # 如果启用了 prompt，则尝试从配置中获取 character_desc（即角色描述），如果未指定，则发出警告。
        if self.prompt_enabled:
            self.prompt = conf().get("character_desc", "")
            if self.prompt == "":
                logger.warn("[BAIDU] Although you enabled model prompt, character_desc is not specified.")
        # 如果 wenxin_model 不为 None，则继续尝试从配置中获取模型名。如果配置中未提供，默认使用 "eb-instant"。
        if wenxin_model is not None:
            wenxin_model = conf().get("baidu_wenxin_model") or "eb-instant"
        # 如果 wenxin_model 为 None，则根据配置项 model 来确定使用的模型：
        else:
            # 如果 model 是 WEN_XIN，则选择 "completions"。
            if conf().get("model") and conf().get("model") == const.WEN_XIN:
                wenxin_model = "completions"
            # 如果 model 是 WEN_XIN_4，则选择 "completions_pro"。
            elif conf().get("model") and conf().get("model") == const.WEN_XIN_4:
                wenxin_model = "completions_pro"
        # 初始化一个 SessionManager 对象，用来管理会话（sessions）。BaiduWenxinSession 是会话类型，wenxin_model 是选择的模型。
        self.sessions = SessionManager(BaiduWenxinSession, model=wenxin_model)
    # reply 方法是实际处理用户查询并生成回复的入口。接收两个参数：query: 用户发送的查询内容（如文本或问题）。
    # context: 可能包含查询的上下文信息。
    def reply(self, query, context=None):
        # acquire reply content
        # 检查 context 是否存在，并且它的类型是 TEXT。如果是文本类型的查询，则进入处理逻辑。
        if context and context.type:
            if context.type == ContextType.TEXT:
                logger.info("[BAIDU] query={}".format(query)) # 打印用户的问题内容。
                # 获取当前会话的 session_id，并初始化回复对象 reply。
                session_id = context["session_id"]
                reply = None
                # 如果指令是 清除记忆，则调用 SessionManager 的 clear_session 方法清除当前会话的记忆，并回复用户“记忆已清除”。
                if query == "#清除记忆":
                    self.sessions.clear_session(session_id)
                    reply = Reply(ReplyType.INFO, "记忆已清除")
                # 如果指令是 #清除所有，则调用 clear_all_session 清除所有人的会话记忆，并回复用户“所有人记忆已清除”。
                elif query == "#清除所有":
                    self.sessions.clear_all_session()
                    reply = Reply(ReplyType.INFO, "所有人记忆已清除")
                # 对于其他查询，使用 session_query 方法获取当前会话（session）的状态，并通过 reply_text 方法生成回复。接
                # 着，提取回复中的信息，如总的 tokens 数量、生成的 tokens 数量和回复内容。
                else:
                    session = self.sessions.session_query(query, session_id)
                    result = self.reply_text(session)
                    total_tokens, completion_tokens, reply_content = (
                        result["total_tokens"],
                        result["completion_tokens"],
                        result["content"],
                    )
                    # 打印调试信息，记录查询、会话 ID 和生成的回复。
                    logger.debug(
                        "[BAIDU] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(session.messages, session_id, reply_content, completion_tokens)
                    )
                    # 如果生成的总 tokens 数量为 0，则返回错误信息；否则，将生成的回复保存到会话中，并回复给用户。
                    if total_tokens == 0:
                        reply = Reply(ReplyType.ERROR, reply_content)
                    else:
                        self.sessions.session_reply(reply_content, session_id, total_tokens)
                        reply = Reply(ReplyType.TEXT, reply_content)
                return reply
            # 如果查询是图像生成类型（IMAGE_CREATE），则调用 create_img 方法生成图像，并返回生成的图像 URL 或错误信息。
            elif context.type == ContextType.IMAGE_CREATE:
                ok, retstring = self.create_img(query, 0)
                reply = None
                if ok:
                    reply = Reply(ReplyType.IMAGE_URL, retstring)
                else:
                    reply = Reply(ReplyType.ERROR, retstring)
                return reply
   #  reply_text 方法用于调用百度文心模型生成文本回复。它接收会话对象 session 和重试次数 retry_count
    def reply_text(self, session: BaiduWenxinSession, retry_count=0):
        try:
            logger.info("[BAIDU] model={}".format(session.model)) # 打印当前使用的模型信息
            # 获取百度的访问令牌（access_token）。如果获取失败，返回错误信息。
            access_token = self.get_access_token()
            if access_token == 'None':
                logger.warn("[BAIDU] access token 获取失败")
                return {
                    "total_tokens": 0,
                    "completion_tokens": 0,
                    "content": 0,
                    }
            #  构建请求 URL，包括模型名称和访问令牌。获取 access_token 后，你可以将它附加到 API 请求的 URL 中，用于调用文心模型的服务。
            # 例如，在 reply_text 方法中，access_token 就会用在调用文心模型的 API 时：这就是获取 access_token 的目的，它是你与百度文心模型
            # 之间进行通信的钥匙。
            url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/" + session.model + "?access_token=" + access_token
            # 设置请求头，指定内容类型为 JSON。根据是否启用 prompt，构建请求的 payload 数据
            headers = {
                'Content-Type': 'application/json'
            }
            payload = {'messages': session.messages, 'system': self.prompt} if self.prompt_enabled else {'messages': session.messages}
            # 发送 POST 请求，调用百度文心 API。
            response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
            # 解析返回的 JSON 响应，并打印响应内容。
            response_text = json.loads(response.text)
            logger.info(f"[BAIDU] response text={response_text}")
            # 提取响应内容，包括生成的文本、总 tokens 数量和生成的 tokens 数量。
            res_content = response_text["result"]
            total_tokens = response_text["usage"]["total_tokens"]
            completion_tokens = response_text["usage"]["completion_tokens"]
            # 打印生成的回复内容，并返回包含 tokens 信息和内容的字典。
            logger.info("[BAIDU] reply={}".format(res_content))
            return {
                "total_tokens": total_tokens,
                "completion_tokens": completion_tokens,
                "content": res_content,
            }
        # 处理异常情况。如果出现错误，记录日志，清除当前会话，并返回错误信息。
        except Exception as e:
            need_retry = retry_count < 2
            logger.warn("[BAIDU] Exception: {}".format(e))
            need_retry = False
            self.sessions.clear_session(session.session_id)
            result = {"total_tokens": 0, "completion_tokens": 0, "content": "出错了: {}".format(e)}
            return result
    # 该方法用于获取百度的 API 访问
    # get_access_token 方法的作用是获取 百度 API 的访问令牌（Access Token），这个令牌用于 授权调用百度文心模型的 API。
    # 在百度的 API 系统中，访问 API 需要使用 access_token，这个令牌是通过提供 API 密钥（API Key） 和 客户端密钥（Secret Key） 获取的。
    # 具体流程是通过百度的 OAuth2.0 授权机制来获取这个访问令牌，之后你可以使用这个 access_token 来访问百度的 AI 服务，如文心（Wenxin）模型。
    # access_token 的作用：验证请求：在向百度文心模型（如对话模型、图像生成模型等）发送请求时，必须提供这个 access_token，以便百度验证你的请求是授权的。
    # 有效期：通常，access_token 会有一定的有效期，通常是 30 天，过期后需要重新获取。
    def get_access_token(self):
        """
        使用 AK，SK 生成鉴权签名（Access Token）
        :return: access_token，或是None(如果错误)
        """
        # 这是百度 API 认证系统的请求地址，用于获取 access_token。
        url = "https://aip.baidubce.com/oauth/2.0/token"
        # grant_type: 指定授权类型，这里使用的是 client_credentials，即客户端凭证授权。
        # client_id: 你的百度 API Key。client_secret: 你的百度 Secret Key。
        params = {"grant_type": "client_credentials", "client_id": BAIDU_API_KEY, "client_secret": BAIDU_SECRET_KEY}
        # 用 requests 库向指定 URL 发送 POST 请求，并携带上面的请求参数。
        # 解析响应：百度的 API 返回的响应是一个 JSON 格式的数据，里面包含了 access_token。通过 json().get("access_token") 
        # 提取 access_token。
        return str(requests.post(url, params=params).json().get("access_token"))
