import time # 导入 Python 的 time 模块，用于处理时间相关的操作

import pip # 导入 pip 模块，pip 是 Python 的包管理工具，可以用来安装、卸载、更新包。
# 从 pip._internal 模块导入 main 函数，并将其重命名为 pipmain。这通常是为了避免与外部 pip 调用冲突。通过这个方法，我们可以
# 使用 pip 内部的接口来进行包安装（注意，这种用法不推荐用于生产环境，因为它直接使用了 pip 的内部 API，可能不稳定）。
from pip._internal import main as pipmain
# 从 common.log 模块导入两个对象：_reset_logger 和 logger。logger 是日志记录器，用于输出日志，而 _reset_logger 函数可能
# 用于在某些情况下重置或更新日志记录器的配置。
from common.log import _reset_logger, logger

# 这个函数用来通过 pip 安装一个包。它接受一个包名 package，并使用 pipmain 来调用 pip 安装该包。这里使用了
# pip._internal.main 来直接调用 pip 内部的安装方法。
def install(package):
    # 这行代码等价于运行 pip install package。pipmain 用来执行安装命令，传递给它的列表 ["install", package] 指定
    # 了 pip 命令的操作（即安装）和目标包。
    pipmain(["install", package])

# 此函数用于安装一个依赖文件中列出的所有 Python 包。file 是一个文件路径，通常是一个包含多个包的 requirements.txt 文件。此函数
# 的作用就是根据文件内容安装或更新这些包。
def install_requirements(file):
    # 这行代码通过 pipmain 执行 pip install -r file --upgrade 命令，-r 表示从文件安装，file 是文件路径，--upgrade 表示如果
    # 依赖已安装，尝试升级到最新版本。
    pipmain(["install", "-r", file, "--upgrade"])
    # 调用 _reset_logger 函数重置日志记录器，可能是为了刷新或重新配置日志设置。
    _reset_logger(logger)

# 检查并安装 dulwich 包（如果它未被安装）。dulwich 是一个用于处理 Git 存储库的 Python 库。
def check_dulwich():
   #  初始化一个标志变量 needwait，用于控制是否需要等待几秒钟后重试安装操作。
    needwait = False
    # 开始一个最多重试 2 次的循环。通过这个循环来尝试安装 dulwich 包，最多重试两次。
    for i in range(2):
        # 如果 needwait 为 True，则程序暂停 3 秒钟。这通常发生在第一次安装包失败时，可能是由于网络或其他临时问题。
        if needwait:
            time.sleep(3) # 暂停程序 3 秒钟，以等待一些系统或网络状况好转。
            needwait = False # 在等待后，重置 needwait 为 False，表示下一次不会再自动等待。
        try:
            # 尝试导入 dulwich 包。如果导入成功，表示该包已经安装，函数直接返回，不做其他操作。
            import dulwich
            return
        # 如果 dulwich 包没有安装，抛出 ImportError 异常，进入异常处理分支。
        except ImportError:
            try:
                install("dulwich") # 如果包未安装，尝试通过 install 函数来安装 dulwich 包。
            except: # 如果安装 dulwich 过程中发生任何错误，设置 needwait = True，表示下一次重试时需要等待。
                needwait = True
    #  再次尝试导入 dulwich 包。这是为了确保包已经安装，如果第一次安装失败，程序会重试。
    try:
        import dulwich
    # 如果第二次仍然无法导入 dulwich，抛出 ImportError 异常并显示错误信息 "Unable to import dulwich"。
    except ImportError:
        raise ImportError("Unable to import dulwich")
