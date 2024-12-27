import requests

from . import storage

class Core(object):
    def __init__(self):
        ''' 
        init 是 core.py 中定义的唯一方法
        alive 是表示核心是否运行的值
            - 你应该调用 logout 方法来改变它
            - 登出后，Core 对象可以重新登录
        storageClass 只使用基本的 Python 类型
            - 所以对于更高级的用法，可以自己继承它
        receivingRetryCount 是接收循环的重试次数
            - 现在是 5，但实际上即使是 1 次也足够
            - 失败就失败
        '''
        self.alive, self.isLogging = False, False
        self.storageClass = storage.Storage(self)
        self.memberList = self.storageClass.memberList
        self.mpList = self.storageClass.mpList
        self.chatroomList = self.storageClass.chatroomList
        self.msgList = self.storageClass.msgList
        self.loginInfo = {}
        self.s = requests.Session()
        self.uuid = None
        self.functionDict = {'FriendChat': {}, 'GroupChat': {}, 'MpChat': {}}
        self.useHotReload, self.hotReloadDir = False, 'itchat.pkl'
        self.receivingRetryCount = 5
    def login(self, enableCmdQR=False, picDir=None, qrCallback=None,
            loginCallback=None, exitCallback=None):
         ''' 
        登录，就像 Web 微信一样
            - 会下载并打开一个二维码
            - 然后扫描状态会被记录，暂停等待你确认
            - 最后会登录，并显示你的昵称
        参数：
            - enableCmdQR: 在命令行显示二维码
                - 可以用整数调整字符的长度
            - picDir: 存储二维码的路径
            - qrCallback: 方法应该接受 uuid，状态，二维码
            - loginCallback: 登录成功后的回调
                - 如果没有设置，屏幕将被清除，二维码也会删除
            - exitCallback: 登出后的回调
                - 包含调用 logout
        用法：
            ..code::python
                import itchat
                itchat.login()
        '''
        raise NotImplementedError()
    def get_QRuuid(self):
         ''' 
        获取二维码的 uuid
            uuid 是二维码的标志
            - 登录时需要先获取 uuid
            - 下载二维码时也需要传入 uuid
            - 检查登录状态时，也需要 uuid
            如果 uuid 超时了，就获取一个新的
        '''
        raise NotImplementedError()
    def get_QR(self, uuid=None, enableCmdQR=False, picDir=None, qrCallback=None):
        ''' 
        下载并显示二维码
            参数：
                - uuid: 如果没有设置，会使用最新获取的 uuid
                - enableCmdQR: 在命令行显示二维码
                - picDir: 存储二维码的路径
                - qrCallback: 方法应该接受 uuid，状态，二维码
        '''
        raise NotImplementedError()
    def check_login(self, uuid=None):
        ''' 
        检查登录状态
            参数：
                - uuid: 如果没有设置，会使用最新获取的 uuid
            返回值：
                - 返回一个字符串
                    - 200: 登录成功
                    - 201: 等待确认
                    - 408: uuid 超时
                    - 0: 未知错误
            处理：
                - 设置 syncUrl 和 fileUrl
                - 设置 BaseRequest
            一直阻塞直到达到上述状态之一
        '''
        raise NotImplementedError()
    def web_init(self):
        ''' 
        获取初始化所需的必要信息
            处理：
                - 设置自己的账户信息
                - 设置 inviteStartCount
                - 设置 syncKey
                - 获取部分联系人信息
        '''
        raise NotImplementedError()
    def show_mobile_login(self):
         ''' 
        显示 Web 微信登录标志
            该标志会在手机微信上方显示
            即使没有调用此函数，标志也会在一段时间后显示
        '''
        raise NotImplementedError()
    def start_receiving(self, exitCallback=None, getReceivingFnOnly=False):
        ''' 
        打开一个线程，用于心跳循环和接收消息
            参数：
                - exitCallback: 登出后的回调
                    - 包含调用 logout
                - getReceivingFnOnly: 如果为 True，不会创建和启动线程，而是返回接收函数
            处理：
                - 消息会被格式化并传递给注册的函数
                - 聊天信息会在接收到相关信息时更新
        '''
        raise NotImplementedError()
    def get_msg(self):
        ''' 
        获取消息
            处理：
                - 方法会阻塞一段时间，直到：
                    - 有新消息接收
                    - 或者任何时候
                - 更新 syncKey 和 synccheckkey
        '''
        raise NotImplementedError()
    def logout(self):
        ''' 
        登出
            如果核心现在是活动的，
            登出会通知微信后台登出
            然后核心会准备好再次登录
        '''
        raise NotImplementedError()
    def update_chatroom(self, userName, detailedMember=False):
        ''' 
        更新聊天室信息
            对于聊天室联系人：
                - 需要更新聊天室信息为详细信息
                - 详细信息包括成员、加密 ID 等
                - 自动更新的心跳循环会更新更详细的信息
                - 成员的 uin 也会被填充
            参数：
                - userName: 聊天室的 'UserName' 键，或者它的列表
                - detailedMember: 是否获取联系人成员信息
        '''
        raise NotImplementedError()
    def update_friend(self, userName):
         ''' 
        更新好友信息
            参数：
                - userName: 好友的 'UserName' 键
        '''
        raise NotImplementedError()
    def get_contact(self, update=False):
         ''' 
        获取部分联系人信息
            参数：
                - update: 如果设置为 True，仅获取已标星的聊天室信息
            返回：
                - 返回聊天室信息列表
        '''
        raise NotImplementedError()
    def get_friends(self, update=False):
        ''' 
        获取好友列表
            参数：
                - update: 如果为 True，仅更新好友列表
            返回：
                - 返回好友信息的字典列表
        '''
        raise NotImplementedError()
    def get_chatrooms(self, update=False, contactOnly=False):
         ''' 
        获取聊天室列表
            参数：
                - update: 如果为 True，仅更新聊天室列表
                - contactOnly: 如果设置为 True，仅返回标星的聊天室
            返回：
                - 返回聊天室信息的字典列表
        '''
        raise NotImplementedError()
    def get_mps(self, update=False):
        ''' 
        获取平台列表
            参数：
                - update: 如果为 True，仅更新平台列表
            返回：
                - 返回平台信息的字典列表
        '''
        raise NotImplementedError()
    def set_alias(self, userName, alias):
        ''' 
        设置好友别名
            参数：
                - userName: 好友信息字典中的 'UserName' 键
                - alias: 新的别名
        '''
        raise NotImplementedError()
    def set_pinned(self, userName, isPinned=True):
          ''' 
        设置好友或聊天室为置顶
            参数：
                - userName: 信息字典中的 'UserName' 键
                - isPinned: 是否置顶
        '''
        raise NotImplementedError()
    def accept_friend(self, userName, v4,autoUpdate=True):
         ''' 
        接受好友请求
            参数：
                - userName: 好友信息字典中的 'UserName' 键
                - status: 
                    - 添加好友时状态应该为 2
                    - 接受好友时状态应该为 3
                - ticket: 问候消息
                - userInfo: 好友的其他信息，用于添加到本地存储
        '''
        raise NotImplementedError()
    def get_head_img(self, userName=None, chatroomUserName=None, picDir=None):
         ''' 
        获取头像
            参数：
                - userName: 好友的 'UserName' 键
                - chatroomUserName: 聊天室的 'UserName' 键
                - picDir: 存储头像的路径
        '''
        raise NotImplementedError()
    def create_chatroom(self, memberList, topic=''):
        ''' 
        创建聊天室
            创建时的调用频率有限制
            参数：
                - memberList: 成员信息字典列表
                - topic: 新聊天室的主题
        '''
        raise NotImplementedError()
    def set_chatroom_name(self, chatroomUserName, name):
         ''' 
        设置聊天室名称
            设置后，聊天室会进行更新，意味着在心跳循环中会返回更详细的信息
            参数：
                - chatroomUserName: 聊天室信息字典中的 'UserName' 键
                - name: 新的聊天室名称
        '''
        raise NotImplementedError()
    def delete_member_from_chatroom(self, chatroomUserName, memberList):
        # 删除聊天室成员
        # 删除规则：
        # - 不能删除自己
        # - 如果删除自己，没人会被删除
        # - 删除频率受限
        # 参数说明：
        # - chatroomUserName: 聊天室信息字典中的 'UserName' 键
        # - memberList: 成员信息字典的列表
        # 定义位置：components/contact.py
        raise NotImplementedError()
    def add_member_into_chatroom(self, chatroomUserName, memberList,
            useInvitation=False):
        # 添加成员到聊天室
        # 添加规则：
        # - 不能添加自己或已经在聊天室中的成员
        # - 如果超过 40 个成员，必须使用邀请
        # - 添加频率受限
        # 参数说明：
        # - chatroomUserName: 聊天室信息字典中的 'UserName' 键
        # - memberList: 成员信息字典的列表
        # - useInvitation: 是否需要邀请
        # 定义位置：components/contact.py
        raise NotImplementedError()
    def send_raw_msg(self, msgType, content, toUserName):
        # 发送原始消息
        # 示例：
        # 通过 @itchat.msg_register(itchat.content.CARD) 注册处理函数
        # 然后用 send_raw_msg 发送消息
        # 注意有一些技巧可以自己发现
        # 定义位置：components/messages.py
        raise NotImplementedError()
    def send_msg(self, msg='Test Message', toUserName=None):
        # 发送纯文本消息
        # 参数说明：
        # - msg: 如果包含非 ASCII 字符，msg 应该是 Unicode 格式
        # - toUserName: 好友字典中的 'UserName' 键
        # 定义位置：components/messages.py
        raise NotImplementedError()
    def upload_file(self, fileDir, isPicture=False, isVideo=False,
            toUserName='filehelper', file_=None, preparedFile=None):
         # 上传文件到服务器并获取 mediaId
        # 参数说明：
        # - fileDir: 准备上传文件的目录
        # - isPicture: 文件是否是图片
        # - isVideo: 文件是否是视频
        # 返回值：
        # - 返回一个 ReturnValue 对象
        # - 如果成功，mediaId 会包含在 r['MediaId'] 中
        # 定义位置：components/messages.py
        raise NotImplementedError()
    def send_file(self, fileDir, toUserName=None, mediaId=None, file_=None):
        # 发送附件
        # 参数说明：
        # - fileDir: 准备上传文件的目录
        # - mediaId: 文件的 mediaId
        #   - 如果设置了 mediaId，则文件不会被上传两次
        # - toUserName: 好友字典中的 'UserName' 键
        # 定义位置：components/messages.py
        raise NotImplementedError()
    def send_image(self, fileDir=None, toUserName=None, mediaId=None, file_=None):
        # 发送图片
        # 参数说明：
        # - fileDir: 准备上传文件的目录
        #   - 如果是 GIF 图片，命名方式应为 'xx.gif'
        # - mediaId: 文件的 mediaId
        #   - 如果设置了 mediaId，则文件不会被上传两次
        # - toUserName: 好友字典中的 'UserName' 键
        # 定义位置：components/messages.py
        raise NotImplementedError()
    def send_video(self, fileDir=None, toUserName=None, mediaId=None, file_=None):
        # 发送视频
        # 参数说明：
        # - fileDir: 准备上传文件的目录
        #   - 如果设置了 mediaId，则不需要设置 fileDir
        # - mediaId: 文件的 mediaId
        #   - 如果设置了 mediaId，则文件不会被上传两次
        # - toUserName: 好友字典中的 'UserName' 键
        # 定义位置：components/messages.py
        raise NotImplementedError()
    def send(self, msg, toUserName=None, mediaId=None):
        # 包装函数，用于所有发送功能
        # 参数说明：
        # - msg: 消息类型通过字符串前缀区分
        #   - 类型字符串列表：['@fil@', '@img@', '@msg@', '@vid@']
        #   - 对应文件、图片、纯文本、视频
        #   - 如果没有匹配的前缀，默认作为纯文本发送
        # - toUserName: 好友字典中的 'UserName' 键
        # - mediaId: 如果设置了 mediaId，则不会重复上传
        # 定义位置：components/messages.py
        raise NotImplementedError()
    def revoke(self, msgId, toUserName, localId=None):
        # 撤回消息
        # 参数说明：
        # - msgId: 服务器上的消息 ID
        # - toUserName: 好友字典中的 'UserName' 键
        # - localId: 本地消息 ID（可选）
        # 定义位置：components/messages.py
        raise NotImplementedError()
    def dump_login_status(self, fileDir=None):
        # 导出登录状态到指定文件
        # 参数说明：
        # - fileDir: 存储登录状态的目录
        # 定义位置：components/hotreload.py
        raise NotImplementedError()
    def load_login_status(self, fileDir,
            loginCallback=None, exitCallback=None):
        # 从指定文件加载登录状态
        # 参数说明：
        # - fileDir: 用于加载登录状态的文件
        # - loginCallback: 登录成功后的回调函数
        #   - 如果未设置，屏幕会被清除并删除二维码
        # - exitCallback: 登出后的回调函数
        #   - 包含调用登出的操作
        # 定义位置：components/hotreload.py
        raise NotImplementedError()
    def auto_login(self, hotReload=False, statusStorageDir='itchat.pkl',
            enableCmdQR=False, picDir=None, qrCallback=None,
            loginCallback=None, exitCallback=None):
        # 自动登录，类似 Web 微信
        # 登录流程：
        # - 下载并打开二维码
        # - 扫描状态被记录，等待确认
        # - 登录成功后显示昵称
        # 参数说明：
        # - hotReload: 启用热重载
        # - statusStorageDir: 存储登录状态的目录
        # - enableCmdQR: 在命令行中显示二维码
        #   - 整数可用于适配不同字符长度
        # - picDir: 存储二维码的目录
        # - loginCallback: 登录成功后的回调函数
        #   - 如果未设置，屏幕将清除并删除二维码
        # - exitCallback: 登出后的回调函数
        #   - 包含登出操作
        # - qrCallback: 接受 uuid, status, qrcode 参数的方法
        # 用法：
        # .. code:: python
        #   import itchat
        #   itchat.auto_login()
        # 定义位置：components/register.py
        # 可以查看源码并根据需求进行修改
        raise NotImplementedError()
    def configured_reply(self):
        # 确定消息类型并回复（如果已定义方法）
        # 然而，我使用了一种奇怪的方式来判断消息是否来自大平台
        # 我还没有找到更好的解决方案
        # 主要问题是手机中添加的新朋友的匹配问题
        # 如果你有好的主意，请报告问题，我将非常感激
        raise NotImplementedError()
    def msg_register(self, msgType,
            isFriendChat=False, isGroupChat=False, isMpChat=False):
        # 消息注册装饰器构造函数
        # 根据给定的信息返回特定的装饰器
        raise NotImplementedError()
    def run(self, debug=True, blockThread=True):
        # 启动自动回复
        # 参数说明：
        # - debug: 如果设置为 True，调试信息会显示在屏幕上
        # 定义位置：components/register.py
        raise NotImplementedError()
    def search_friends(self, name=None, userName=None, remarkName=None, nickName=None,
            wechatAccount=None):
        # 搜索好友
        # 参数说明：
        # - name: 好友的名称
        # - userName: 好友的用户名
        # - remarkName: 好友的备注名称
        # - nickName: 好友的昵称
        # - wechatAccount: 好友的微信号
        # 返回通过 storageClass 对象的 search_friends 方法进行的搜索结果
        return self.storageClass.search_friends(name, userName, remarkName,
            nickName, wechatAccount)
    def search_chatrooms(self, name=None, userName=None):
        # 搜索聊天群
        # 参数说明：
        # - name: 聊天群名称
        # - userName: 聊天群的用户名
        # 返回通过 storageClass 对象的 search_chatrooms 方法进行的搜索结果
        return self.storageClass.search_chatrooms(name, userName)
    def search_mps(self, name=None, userName=None):
        # 搜索公众号
        # 参数说明：
        # - name: 公众号名称
        # - userName: 公众号的用户名
        # 返回通过 storageClass 对象的 search_mps 方法进行的搜索结果
        return self.storageClass.search_mps(name, userName)
