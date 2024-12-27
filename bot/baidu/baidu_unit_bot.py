# encoding:utf-8

import requests

from bot.bot import Bot
from bridge.reply import Reply, ReplyType

# 百度 UNIT（Unified Natural Language Understanding）是百度的一个对话系统框架，主要用于自然语言处理（NLP）任务，尤其是对话生成、语义理解等。
# 这段代码实现了一个基于百度 UNIT（对话模型）的自动回复机器人 BaiduUnitBot，它继承自 Bot 类并使用百度的 UNIT API 来处理用户的对话请求。
# Baidu Unit对话接口 (可用, 但能力较弱)
class BaiduUnitBot(Bot):
    # reply 方法是接收用户查询并返回响应的核心方法。它接收两个参数：query: 用户输入的内容（可能是对话中的一部分或问题）。
    # context: 上下文对象，可能包含与该查询相关的历史信息（可选，当前代码未使用 context）。
    def reply(self, query, context=None):
        token = self.get_token() # 调用 get_token 方法获取 Access Token。这个令牌将用于授权访问百度 UNIT API。
        # 构建 API 请求的 URL，access_token 用于身份验证，确保请求是授权的。
        url = "https://aip.baidubce.com/rpc/2.0/unit/service/v3/chat?access_token=" + token
        # 构建请求数据：post_data 是一个包含用户查询的 JSON 字符串。这个字符串格式化后包含了以下信息：
       # "version": "3.0"：API 的版本号。"service_id": "S73177"：指向特定的服务ID，通常是与你的应用或模型相关的标识。
        # "session_id": ""：会话 ID，这里为空，表示新会话。 log_id": "7758521"：日志 ID，用于追踪请求和响应。
        # "skill_ids": ["1221886"]：技能 ID，表示请求所调用的具体技能或模型
       #  "request": {}：请求内容："terminal_id": "88888"：设备 ID，可能代表客户端终端。
        # "query": query：用户的查询内容，实际会被替换为 query 变量（即用户输入的问题或请求）。
      #  "hyper_params": {"chat_custom_bot_profile": 1}：额外的自定义参数，这里 chat_custom_bot_profile 表示使用自定义的聊天机器人配置。
        # post_data 依然是一个字符串类型，尽管它被括号包裹起来了。在 Python 中，使用括号括起的多行代码可以提高代码的可读性，但并不会改变表达式的类型。
        post_data = (
            '{"version":"3.0","service_id":"S73177","session_id":"","log_id":"7758521","skill_ids":["1221886"],"request":{"terminal_id":"88888","query":"'
            + query
            + '", "hyper_params": {"chat_custom_bot_profile": 1}}}'
        )
        print(post_data) # 打印构建的请求数据，便于调试和查看请求格式。
        # 设置 HTTP 请求头，指定内容类型为 application/x-www-form-urlencoded。这通常用于传递表单数据，但这里也用于发送 JSON 数据。
        # 这是设置请求头，告诉服务器你发送的数据是 表单数据 的类型。具体来说，Content-Type 头部字段用于告知服务器请求体中的数据格式，以便服务器能够正确地解析数据。
        # Content-Type: application/x-www-form-urlencoded： 这是标准的 表单提交数据格式，通常用于 HTML 表单提交。当你提交表单时，数据会
        # 被编码成 key1=value1&key2=value2 的格式，并作为请求体的一部分发送到服务器。
        # 在你这段代码中，虽然请求的数据是 JSON 格式，但却将 Content-Type 设置为 application/x-www-form-urlencoded，这实际上
        # 是一个不常见的做法。通常，对于 JSON 数据，Content-Type 应该设置为 application/json。不过，具体的接口要求可能决定了需要使用哪种格式。
        # 有些 API 接口可能要求数据采用 application/x-www-form-urlencoded 的格式，而不管实际的数据格式是 JSON 还是其他格式。比如某些服
        # 务器端代码或者框架会期望接收 表单格式 的数据，即使其中包含了 JSON 字符串。为了兼容这种情况，可能会选择将 JSON 字符串作为一个表单参数传递。
        # 例如，可能是发送一个 URL 编码的请求，其中 JSON 数据会作为表单字段的一部分
        headers = {"content-type": "application/x-www-form-urlencoded"}
        # 发送 POST 请求到百度 UNIT API。请求的 URL 包含 access_token，请求体为 post_data，并带有适当的请求头。
        # 在这行代码中，post_data 是一个 JSON 字符串。使用 encode() 方法后，它会被编码成 字节串（bytes）。默认情况下，Python 的 
        # .encode() 方法会将字符串编码为 UTF-8 格式。
        # encode() 方法是将字符串从 文本（str） 转换为 字节（bytes） 的过程，转换时默认使用 UTF-8 编码。
        # 为什么需要 .encode()？HTTP 请求的 数据部分（如 POST 请求的 body）是通过字节流传输的，而不是普通的字符串。因此，必须将字符串转
        # 换为字节流才能通过网络发送。.encode() 就是将字符串转化为字节串的过程。
        response = requests.post(url, data=post_data.encode(), headers=headers)
        # 如果收到有效响应，解析 JSON 响应并提取所需的回复内容：esponse.json()：将响应的 JSON 内容转换为字典。
        # ["result"]["context"]["SYS_PRESUMED_HIST"][1]：根据百度 UNIT 的 API 文档，SYS_PRESUMED_HIST 是历史对话的一个列表
        # ，返回的是一个可能的系统回复。这里 [1] 取的是列表中的第二个元素，通常是机器人生成的回复。
        # 创建一个 Reply 对象，指定回复类型为文本（ReplyType.TEXT），并将解析出的回复内容作为机器人的回复。
        if response:
            reply = Reply(
                ReplyType.TEXT,
                response.json()["result"]["context"]["SYS_PRESUMED_HIST"][1],
            )
            return reply

    def get_token(self):
        access_key = "YOUR_ACCESS_KEY"
        secret_key = "YOUR_SECRET_KEY"
        # 构建获取 access_token 的请求 URL。URL 中包含：
        # grant_type=client_credentials：表示使用客户端凭证进行授权（即不需要用户交互的授权方式）。
       #  client_id 和 client_secret：通过百度云提供的 API 密钥获取。
        host = "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=" + access_key + "&client_secret=" + secret_key
        response = requests.get(host) # 发送一个 GET 请求到百度的 OAuth 2.0 授权接口，请求生成 access_token。
        # 如果响应成功，打印响应的 JSON 内容（便于调试），并从中提取 access_token 返回。
        # access_token 是一个字符串，在后续的 API 请求中需要使用它来进行身份验证。
        if response:
            print(response.json())
            return response.json()["access_token"]
