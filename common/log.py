import logging
import sys
def _reset_logger(log):
    #　清理现有处理器 (handlers)
    # 确保在重新配置之前，所有旧的处理器都被正确地清理掉，避免重复或冲突的日志输出。
    # 关闭资源以避免浪费，并确保在重新配置日志记录器时不会产生冲突或重复的日志输出。
    for handler in log.handlers:
        handler.close()
        log.removeHandler(handler)
        del handler
    log.handlers.clear() # 清空 handlers 列表，确保没有任何残留的处理器。
    # 确保日志只由当前配置的处理器处理，不会被其他地方的处理器再次处理，避免重复日志。
    log.propagate = False # 禁止日志传播 (propagate)
    # 创建并配置控制台处理器
    console_handle = logging.StreamHandler(sys.stdout)
    console_handle.setFormatter(
        logging.Formatter(
            "[%(levelname)s][%(asctime)s][%(filename)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    # 创建并配置文件处理器 (file_handle)
    file_handle = logging.FileHandler("run.log", encoding="utf-8")
    file_handle.setFormatter(
        logging.Formatter(
            "[%(levelname)s][%(asctime)s][%(filename)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    # 添加处理器到日志记录器,使日志记录器能够同时将日志输出到文件和控制台。
    log.addHandler(file_handle)
    log.addHandler(console_handle)

def _get_logger():
    log = logging.getLogger("log")
    _reset_logger(log)
    log.setLevel(logging.INFO) # info级别
    return log
# 日志记录器
logger = _get_logger()
