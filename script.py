import argparse
import sys
import signal
import os
import logging
def main():
    # parser = argparse.ArgumentParser(description="处理命令行参数")
    
    # # 添加 --cmd 参数，默认情况下，action='store_true' 意味着如果该参数未被提供，则其值为 False；如果提供了该参数（无论是否有值），则其值变为 True。
    # #设置 default=True，那么意味着当用户没有显式提供 --cmd 参数时，默认情况下 args.cmd 将为 True
    # parser.add_argument('--cmd', action='store_true', help='使用终端通道',default=True,)
    
    # args = parser.parse_args()

    # # 根据 --cmd 参数设置 channel_name
    # channel_name = "terminal" if args.cmd else "default"
    # signal.pause() 会让进程进入休眠状态，直到接收到一个信号。这个信号必须是已经被注册过的（即有对应的处理器）。
    # print(f"Channel name set to: {channel_name}")
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    while True:
        signal.pause()
if __name__ == "__main__":
    main()