from common.expired_dict import ExpiredDict
from common.log import logger
from config import conf
# 举例：
# 假设你在与一个智能客服机器人进行对话。整个对话过程中，机器人和你之间会交换多轮消息，每一轮消息都是基于前一轮的上下文生成的。为了让机器人理解并记住你之
# 前说过的话，它会维护一个会话。
# 会话开始：
# 你与机器人开始对话，机器人根据系统提示（如 system_prompt）生成回答。
# 会话ID被分配给这个新的对话，例如：session_id="12345"。
# 你发送查询：
# 你向机器人询问一个问题，例如：“今天的天气怎么样？”
# 机器人将你这个查询记录下来（消息角色为 user），并根据该查询生成回复（消息角色为 assistant）。
# 会话持续：
# 如果对话继续，机器人会基于之前的对话（即用户的查询和机器人的回复）生成更准确的回复。
# 系统会通过 session_id 来持续跟踪这个对话，确保后续的回复能理解你的问题的上下文，而不仅仅是孤立地回答每个问题。
# 会话结束：
# 当你结束与机器人的对话时，或者如果会话超时，SessionManager 可以清理该会话，删除记录，并释放资源。
# 会话的功能：
# 上下文跟踪：
# 会话使得机器人可以跟踪和记住上下文，这样机器人在回复用户时能够基于过去的对话生成更加连贯、自然的回答。
# 多轮对话：
# 在多轮对话中，用户每次的查询和机器人的回复都依赖于之前的对话内容。会话用于存储这些交互，保持对话的一致性。
# 过期和清理：
# 会话也可能有过期时间（expires_in_seconds），如果用户在一段时间内没有与系统交互，会话可能会自动失效。会话管理器会在需要时清理过期的会话。
# 令牌管理：
# 对话中的每条消息（如查询、回复）通常会被转换成“令牌”（tokens）。会话可以管理这些令牌的数量，以确保对话不会超出API或系统的令牌限制，避免计算资源浪费。
# 总结：
# 在这段代码中，“会话”是指一组由用户和机器人（或系统）之间的交互消息组成的记录，它跟踪用户输入、机器人的回复、以及相关的上下文信息（例如系统提示）。
# 会话管理器负责创建、更新、删除会话，并控制会话的生命周期及令牌的使用。在整个对话过程中，会话帮助系统理解跨多个交互的上下文，生成更加自然且有针对性的回答。
# 和机器人的多个轮次的对话通常只属于一个 session（会话）。会话（session）代表着用户和机器人之间的一段持续的对话交互，通常会跨多个轮次。每一轮对话，包括
# 用户的查询和机器人的回复，都属于同一个会话，它们共享相同的上下文。
# 为什么多个轮次属于同一个 Session？
# 上下文连续性：
# 在多个轮次的对话中，机器人的回答通常是基于之前的对话内容生成的。会话允许系统追踪这些对话上下文，确保每轮对话都能理解和考虑先前的内容。每个新的查询和回复都会
# 根据之前的消息进行调整，以便机器人能够给出相关和连贯的回答。
# 令牌和消息管理：
# 每个会话中的消息都会被分配令牌（tokens）。令牌数通常会影响模型的响应质量或最大字数限制，因此系统会跟踪会话的令牌使用，避免达到模型限制。会话管理器负责确保
# 会话中所有消息的令牌总数不会超过限制（例如，每个会话允许的最大令牌数）。
# 系统提示和初始设置：
# 会话通常会有一个系统提示信息（system_prompt），它是在会话开始时由系统或开发者定义的，影响机器人的行为和回答风格。这个系统提示会在整个会话中保持一致，除非有
# 显式修改（例如，用户更新 system_prompt）。多个轮次的对话依赖于这个提示信息，因此它是跨轮次共享的。
# 假设你和机器人进行如下对话：
# 用户输入：“你好，今天的天气怎么样？”
# 机器人基于系统提示（例如："你是一个天气助手"）来生成回复。
# 机器人回复：“今天的天气晴，温度25°C。”
# 机器人将这个回复记录在会话中，并将用户的查询也记录下来，形成一条消息历史。
# 用户输入：“明天呢？”
# 机器人会基于之前的对话上下文（用户曾问过天气）生成相关的回复，而不是单独理解为一个全新的查询。
# 机器人回复：“明天会有小雨，温度22°C。”
# 机器人将这个新回复和用户的查询一起记录下来，继续扩展会话历史。
# 在这里，所有的这些互动（用户查询和机器人的回复）都属于同一个会话（session）。会话的作用是保证：
# 机器人能够理解上下文（例如，理解“明天”的问题是指天气的后续问题，而不是完全新的查询）。
# 每次查询和回复都是基于会话中的先前信息生成的。
# 会话的结束：
# 如果用户结束了对话，或者一段时间内没有交互，系统可能会自动清除会话。
# 也可以通过一些显式的命令（如 #清除记忆）来清除会话。
# 在群聊中，会话（session） 的概念仍然是适用的，但它的管理和结构可能会有所不同。群聊中的会话通常需要考虑以下几个方面：
# 1. 每个用户一个会话：
# 在群聊中，通常每个用户会有一个独立的会话（session）。这意味着每个用户与机器人之间的对话是独立的，每个用户的查询和机器人的回复都属于不同的会话。
# 比如，如果有三个用户（User A、User B 和 User C），他们各自与机器人之间的对话会有各自的 session_id。机器人会为每个用户维护一个单独的会话，以
# 便跟踪他们的历史查询和上下文。
# 2. 群聊会话的管理：
# 群聊中的消息会根据用户的身份、内容、以及是否需要响应等因素进行管理。机器人可能会需要分辨出来自不同用户的查询，并为每个用户维护独立的消息历史。
# 比如，机器人收到来自用户 A 的问题：“今天的天气怎么样？”之后，机器人会将这个查询和对应的回复加入到 A 的会话中。而如果用户 B 在同一时间问：
# “明天的天气如何？”，机器人会为用户 B 创建或更新另一个会话，记录该查询及回复。
# 3. 群聊上下文的维持：
# 对于群聊来说，机器人通常需要为每个用户维护一个独立的上下文，因为每个用户可能提出不同的问题，机器人需要区分对待。
# 如果机器人需要基于群聊中的消息来生成回复，它通常会针对每个用户的输入生成一个响应，而不是统一地根据群聊中的所有内容来推理。除非机器人
# 需要根据群聊中的某个共同话题进行群体回复。
# 4. 群聊的共同回复：
# 如果机器人需要对群聊中的所有成员做出共同的回复（例如，群组消息、公告等），那么机器人会根据群聊的上下文或用户的群体需求生成一个回复，并发送给所有人。
# 在这种情况下，机器人也可以使用某些群聊特定的上下文信息来生成回复，但这通常是全局性的，而不是针对单个用户的会话。
# 举个例子：
# 假设你在一个群聊中，机器人为每个用户维护一个单独的会话：
# 用户 A 提问：“今天的天气怎么样？”
# 机器人会创建或更新用户 A 的会话（session_id 为 A 的唯一标识符），并生成针对用户 A 的回复：“今天的天气晴，温度25°C。”
# 用户 B 提问：“明天呢？”
# 机器人会创建或更新用户 B 的会话，生成针对用户 B 的回复：“明天会有小雨，温度22°C。”
# 群聊中的公告：
# 如果管理员或机器人在群聊中发布公告，如：“大家注意，明天的活动安排已更新，请查收。” 这种消息可能会不基于单个用户的会话，而是通过群聊的整体上下文来处理并发送给所有用户。
# 机器人回复：
# 对于群聊中的其他用户（例如用户 C），机器人需要知道他们是否对当前话题感兴趣，并根据他们的会话上下文生成相应的回答。
# 假设在一个群聊中，有三个用户：User A、User B 和 User C。每个用户和机器人的对话会有独立的 session_id。
# 用户 A：与机器人进行多轮对话。
# 第一轮：用户 A 问：“今天的天气怎么样？”
# 第二轮：用户 A 问：“明天呢？”
# 这些消息都属于用户 A 的会话，并在 session_id 为 A 的会话中管理。
# 用户 B：与机器人进行另一轮对话。
# 第一轮：用户 B 问：“我应该穿什么衣服？”
# 第二轮：用户 B 问：“适合的颜色是什么？”
# 这些消息属于用户 B 的会话，存储在 session_id 为 B 的会话中。
# 用户 C：与机器人进行独立对话。
# 第一轮：用户 C 问：“今晚吃什么？”
# 这些消息属于用户 C 的会话，存储在 session_id 为 C 的会话中
# 会话管理器（SessionManager）会管理所有用户的会话，例如：
# 为用户 A 创建/获取会话：session = session_manager.build_session(session_id="A")
# 为用户 B 创建/获取会话：session = session_manager.build_session(session_id="B")
# 为用户 C 创建/获取会话：session = session_manager.build_session(session_id="C")
# 这样，无论是 用户 A、用户 B 还是 用户 C，他们每个人都有自己的会话历史（会话上下文）。会话管理器会确保每个用户的会话数据不混
# 合，每个用户的查询和机器人的回答都在各自的会话中处理。
# 您提到的概念非常好，确实可以通过类比来理解：“会话” 和 “Web中的会话（session）” 在很多方面是类似的，尤其是在每个用户与系统之间维持一个独立的
# 、唯一的会话上下文。
# 1. Web中的会话（Session）
# 在Web应用中，Session 通常指的是在用户与服务器之间的一系列交互过程中的状态保持。每个用户在访问网站时，都会有一个唯一的 session_id，这个 
# session_id，用于跟踪用户的对话历史。 被用来识别该用户的请求，并将这个请求与该用户的会话状态（如登录信息、购物车内容等）关联起来。直到用户退
# 出或会话过期，整个会话才会结束。
# 唯一 session_id：每个用户在会话期间拥有一个唯一的 session_id，用于跟踪用户的状态和数据。
# 多次交互：在用户与服务器的交互过程中，session_id 始终保持不变，即使用户发送多个请求，所有请求都属于同一个会话。
# 2. 机器人中的会话（Session）
# 在对话系统中，比如与聊天机器人互动时，会话 的概念也类似。每个用户和机器人的多轮对话被视为一个会话，整个会话通过一个唯一的 session_id 
# 来标识。在多轮对话中，用户可以提出多个问题，机器人根据上下文（之前的对话）来生成回答，直到会话结束或被清除。
# 唯一 session_id：每个用户与机器人之间的对话都有一个唯一的 session_id，这个 session_id 用来维持该用户与机器人之间的上下文（包括查询历史、机器人回复等）。
# 多轮对话：即使用户提出多个问题，所有问题和答案都属于同一个会话。机器人通过持续的上下文跟踪来理解用户的意图，并在对话中做出响应。
# 类比与区别：
# 相似之处：
# 唯一标识：就像Web会话中的 session_id 一样，聊天机器人中的每个会话也有一个唯一的 session_id，用于跟踪用户的对话历史。
# 多轮交互：无论是Web会话还是机器人会话，都可以包含多轮交互。Web应用可能有多个页面请求，而聊天机器人会话则是用户的多轮问题与机器人回答。
# 持续性状态：无论是Web会话还是机器人会话，在整个会话期间，用户的状态或上下文会持续保持，直到会话结束（例如用户退出或会话过期）。
# 区别：
# 会话的“结束”：
# 在Web应用中，用户通常明确地“退出”会话（比如注销或者关闭浏览器）。而在聊天机器人中，会话的结束通常取决于具体的业务逻辑。例如，用户明确发出“清
# 除记忆”命令，或者会话超时等情况下，机器人会清除或结束当前会话。
# 会话的上下文：
# Web会话通常包含诸如用户认证信息、用户选择的商品、页面的状态等数据，而机器人会话的上下文更关注用户与机器人的对话历史（如问答、聊天记录、上下文信息）。
# 举个例子：
# 假设您是一个用户，与机器人进行对话：
# 第一轮对话：
# 用户：你今天有什么推荐的电影吗？
# 机器人：今天有几部不错的电影，像《XXXX》和《YYYY》都很受欢迎。
# 这一轮对话创建了一个会话，机器人会将用户的查询和回复添加到会话历史中，保持对话上下文。
# 第二轮对话：
# 用户：那推荐一下适合家庭看的电影。
# 机器人：推荐《ZZZZ》，这是一部家庭喜剧片，适合全家观看。
# 在第二轮中，虽然用户提出了一个新的问题，但这个问题仍然属于同一个会话，机器人会利用 第1轮的上下文 来理解用
# 户的偏好，给出更符合用户需求的回答。
# 第三轮对话：
# 用户：明天上映的电影有哪些？
# 机器人：明天有《AAAA》和《BBBB》上映，推荐给你。
# 机器人继续保持同一个 session_id，并根据此前的对话更新上下文，给出合适的回答。
# 总结：
# 会话（Session） 是用户与机器人之间持续的对话过程，整个过程中机器人的回答会根据用户的历史提问进行调整。
# 在 Web会话 中，session_id 通过浏览器的 cookie 或 HTTP 头部来维持，而在 机器人会话 中，session_id 用来标识用户与机器人的对话历史。
# 不管是 Web 还是机器人，多轮对话都属于同一个会话，只要会话没有被清除或者超时。
# Session 类表示一个单独的对话会话
# 会话（Session）指的是与用户或其他系统交互的一段时间内的对话状态和上下文。它通常用于跟踪和管理与某个用户的多轮对话，记录用户输入的查询、系统或机器人回
# 复的信息、以及相关的上下文（例如，系统的提示信息或历史交互内容）。会话的目的在于让系统能够记住并理解跨多个交互的上下文，以便生成更符合当前情境的回应。
# 会话包含以下几个重要方面：
# 会话标识符（session_id）：
# 每个会话都有一个唯一的标识符 session_id，用于区分不同的会话。这通常是一个唯一的字符串或数字，表示一个特定用户或一段特定交互的会话。
# 消息历史（messages）：
# 会话中的消息记录了所有的用户查询和机器人回复。每条消息都有一个 role 字段，表示该消息是由谁发出的：
# "user"：用户的输入,"assistant"：机器人的回复。 "system"：系统的提示信息（例如初始的系统设置或规则）。
# 系统提示信息（system_prompt）：
# 每个会话可能会有一条“系统提示”信息，它是与会话相关的初始设置信息或指引，通常会影响机器人如何生成回应。例如，系统提示可以定义
# 机器人的角色、语气、风格等。
# 会话管理
# 会话不仅仅包含消息，还需要管理会话的生命周期。例如，SessionManager 负责创建、查找、更新、删除会话，并可以在会话超时后清理无效的会话。
# 会话管理器还负责跟踪和计算消息的令牌数，确保会话内容不会超过某个预定的长度或令牌数限制。
class Session(object):
    # __init__ 是类的构造函数，用来初始化一个新的会话实例。
    def __init__(self, session_id, system_prompt=None):
        self.session_id = session_id # session_id：每个会话的唯一标识符。
        self.messages = [] # messages：保存会话中的所有消息。
       #  system_prompt：用于初始化系统提示信息。如果没有传入 system_prompt，则从配置中读取 character_desc。
        if system_prompt is None:
            self.system_prompt = conf().get("character_desc", "")
        else:
            self.system_prompt = system_prompt

    # reset 方法用于重置当前会话，将会话中的所有消息清空，并重新设置为系统提示信息（system_prompt）。这里会
    # 话的第一条消息是系统提示信息，角色为 "system"。
    def reset(self):
        system_item = {"role": "system", "content": self.system_prompt}
        self.messages = [system_item]
    # set_system_prompt 方法用于更新 system_prompt 并重置会话。
    # 更新后，会调用 reset 方法，清空并重新初始化会话。
    def set_system_prompt(self, system_prompt):
        self.system_prompt = system_prompt
        self.reset()
    # add_query 方法用于将用户的查询（query）添加到会话中的 messages 列表里。每个消息都有一个角色 (role)，这里是
    # "user"，表示这是用户的输入。
    def add_query(self, query):
        user_item = {"role": "user", "content": query}
        self.messages.append(user_item)
    # add_reply 方法用于将助手的回复（reply）添加到会话中的 messages 列表里。每个消息的角色 (role) 是
    # "assistant"，表示这是机器人的回复。
    def add_reply(self, reply):
        assistant_item = {"role": "assistant", "content": reply}
        self.messages.append(assistant_item)
    # 这是一个抽象方法，表示丢弃超出最大令牌数的消息。这个方法在子类中实现。
    def discard_exceeding(self, max_tokens=None, cur_tokens=None):
        raise NotImplementedError
    # 这是一个抽象方法，表示计算当前会话中的令牌数。在子类中实现。
    def calc_tokens(self):
        raise NotImplementedError
# SessionManager 类则负责管理多个会话。
class SessionManager(object):
   #  __init__ 是 SessionManager 类的构造函数，用于初始化会话管理器。
    def __init__(self, sessioncls, **session_args):
        if conf().get("expires_in_seconds"):
            sessions = ExpiredDict(conf().get("expires_in_seconds"))
        else:
            sessions = dict()
        
        self.sessions = sessions
        # sessioncls：会话类，通常为 Session 类。sessioncls 是动态传入的，可以灵活创建不同类型的会话。
        self.sessioncls = sessioncls
        self.session_args = session_args # session_args：会话类的额外参数，例如会话初始化时需要的配置。
    # build_session 方法用于根据 session_id 创建或获取现有的会话。
   
    def build_session(self, session_id, system_prompt=None):
        # 如果 session_id 为 None，直接创建一个新的会话。
        if session_id is None:
            return self.sessioncls(session_id, system_prompt, **self.session_args)
        # 如果 session_id 不在 sessions 字典中，创建新的会话并加入字典。
        if session_id not in self.sessions:
            self.sessions[session_id] = self.sessioncls(session_id, system_prompt, **self.session_args)
        # 如果 session_id 存在，并且传入了新的 system_prompt，则更新该会话的 system_prompt 并重置会话。
        elif system_prompt is not None:  
            self.sessions[session_id].set_system_prompt(system_prompt)
        session = self.sessions[session_id]
        return session
    # session_query 方法处理用户查询。
    def session_query(self, query, session_id):
        session = self.build_session(session_id) # 通过 session_id 获取或创建会话，然后将查询添加到该会话。
        session.add_query(query)
       # 获取最大令牌数 max_tokens 并计算当前会话中的令牌数。如果令牌数超出最大值，调用 discard_exceeding 丢弃多余的部分。
        try:
            max_tokens = conf().get("conversation_max_tokens", 1000)
            total_tokens = session.discard_exceeding(max_tokens, None)
            logger.debug("prompt tokens used={}".format(total_tokens))
        except Exception as e:
            logger.warning("Exception when counting tokens precisely for prompt: {}".format(str(e)))
        return session
    # session_reply 方法处理机器人的回复。
    def session_reply(self, reply, session_id, total_tokens=None):
        # 获取或创建会话并将回复添加到会话。
        session = self.build_session(session_id)
        session.add_reply(reply)
        # 计算会话的令牌数并根据需要丢弃多余的令牌。
        try: 
            max_tokens = conf().get("conversation_max_tokens", 1000)
            tokens_cnt = session.discard_exceeding(max_tokens, total_tokens)
            logger.debug("raw total_tokens={}, savesession tokens={}".format(total_tokens, tokens_cnt))
        except Exception as e:
            logger.warning("Exception when counting tokens precisely for session: {}".format(str(e)))
        return session
    # clear_session 方法用于删除指定 session_id 的会话。如果该会话存在，就从 sessions 中删除它。
    def clear_session(self, session_id):
        if session_id in self.sessions:
            del self.sessions[session_id]
    # clear_all_session 方法用于清空所有会话，即删除 sessions 字典中的所有条目。
    def clear_all_session(self):
        self.sessions.clear()
