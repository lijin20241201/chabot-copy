from datetime import datetime, timedelta

# 这段代码定义了一个 ExpiredDict 类，继承自 Python 内建的 dict，它实现了一个带有过期时间的字典。每个存储在 ExpiredDict 
# 中的值都有一个与之关联的过期时间，超过这个时间后，值就会被删除，并在访问时抛出 KeyError。
class ExpiredDict(dict):
    # __init__ 是 ExpiredDict 类的构造函数。当你创建一个 ExpiredDict 实例时，必须传入一个 expires_in_seconds 参数，表
    # 示字典中每个元素的过期时间（单位是秒）。
    def __init__(self, expires_in_seconds):
        super().__init__() # super().__init__() 调用父类 dict 的构造函数来初始化字典本身。
        self.expires_in_seconds = expires_in_seconds # self.expires_in_seconds 存储了每个条目的过期时间。
    # __getitem__ 是对字典 get 操作的重载，允许你通过 ExpiredDict[key] 获取值。
    def __getitem__(self, key):
        # super().__getitem__(key) 调用父类 dict 的 __getitem__ 方法，返回存储在该键下的 value 和 expiry_time（
        # 元组形式 (value, expiry_time)）。
        value, expiry_time = super().__getitem__(key)
        # 如果当前时间（datetime.now()）大于 expiry_time，说明这个值已经过期，于是删除这个条目并抛出 KeyError。
        if datetime.now() > expiry_time:
            del self[key]
            raise KeyError("expired {}".format(key))
        # 如果值没有过期，更新字典条目，将新的过期时间设置进去（通过调用 __setitem__），并返回该值。
        self.__setitem__(key, value)
        return value
    # __setitem__ 是对字典 set 操作的重载，允许你通过 ExpiredDict[key] = value 设置键值对。
    def __setitem__(self, key, value):
        # 计算过期时间（当前时间加上指定的 expires_in_seconds）。
       # timedelta(seconds=self.expires_in_seconds) 用于计算一个时间段（即过期时间），该时间段是从当前时间 
        # datetime.now() 开始，持续 self.expires_in_seconds 秒。
        # timedelta 是一个表示时间差的类，它的常见用法是加减日期或时间。
        expiry_time = datetime.now() + timedelta(seconds=self.expires_in_seconds)
        # 使用 super().__setitem__(key, (value, expiry_time)) 调用父类 dict 的 __setitem__ 方法，将值和过期时间元组存储到字典中。
        super().__setitem__(key, (value, expiry_time))
    # get 方法尝试获取键对应的值，如果键不存在或值已过期，会返回 default 参数（默认为 None）。
    def get(self, key, default=None):
        # 它通过 self[key] 调用 __getitem__ 获取值，如果出现 KeyError（比如键不存在或过期），则返回默认值。
        try:
            return self[key]
        except KeyError:
            return default
    # __contains__ 方法重载了 in 运算符，用于判断某个键是否在字典中有效。
    def __contains__(self, key):
        # 它通过 self[key] 来访问值，如果值不存在或者过期，就会抛出 KeyError，此时返回 False，否则返回 True。
        try:
            self[key]
            return True
        except KeyError:
            return False
    # keys 方法返回一个字典中所有有效的键
    # 首先，通过 super().keys() 获取所有的键，然后通过列表推导式检查这些键是否有效（即是否未过期）。如果键有效，就将它加入返回的列表。
    def keys(self):
        keys = list(super().keys())
        return [key for key in keys if key in self]
    # items 方法返回一个包含所有有效键值对的列表。
    # 它通过调用 self.keys() 获取所有有效的键，然后构造一个元组 (key, value) 并返回。
    def items(self):
        return [(key, self[key]) for key in self.keys()]
   #  __iter__ 方法重载了 iter() 函数，用于返回字典中所有有效键的迭代器。
   # 它通过调用 self.keys() 返回有效键的列表，再调用 __iter__() 返回其迭代器。
    def __iter__(self):
        return self.keys().__iter__()
