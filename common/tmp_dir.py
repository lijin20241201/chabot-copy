import os
import pathlib

from config import conf

# 临时目录
class TmpDir(object):
    tmpFilePath = pathlib.Path("./tmp/") # tmpFilePath 是一个类属性（class attribute）,它会被类的所有实例共享。
    def __init__(self):
        pathExists = os.path.exists(self.tmpFilePath)
        #  如果临时目录不存在,就创建
        if not pathExists: 
            os.makedirs(self.tmpFilePath)
    def path(self):
        return str(self.tmpFilePath) + "/"
