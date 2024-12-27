# import heapq 是 Python 标准库中的一个模块，提供了堆队列算法（Heap Queue Algorithm）的实现。堆是一种特殊的完全二叉树结构，通常用来实现优先队列。
# 优先队列：堆可以用来实现优先队列，在这种队列中，元素的优先级由其值决定。
# 排序：虽然堆的排序效率比传统的排序算法（如 sorted）稍差，但也可以用来进行部分排序或在线排序（比如逐步从堆中弹出元素，获得有序列表）。
import heapq

# 这个 SortedDict 类是一个扩展自 Python 标准 dict 类型的自定义字典，它对字典中的元素按照某个排序函数进行排序。该字典的键值对是
# 根据排序条件动态维护的，每当插入或删除元素时，会根据指定的排序规则更新字典的排序顺序。
# SortedDict 是一个自定义的字典类，扩展了字典的功能，使其支持动态排序。它通过 heapq 实现了一个最小堆来存储字典项，并使用一个排序函数 
# ort_func 来确定每个元素的优先级。每当字典项发生更改时，堆会被更新，并且字典的键值对会按照排序规则进行排序，keys() 和 items() 方法可以返回已排序的键和值。
# 这个类的主要优点是：
# 支持动态更新排序，插入、删除、更新字典项时会保持排序。
# 可以通过 reverse 控制排序的顺序。
# 通过 ort_func 灵活指定排序规则。
class SortedDict(dict):
    # ort_func: 默认值是 lambda k, v: k，即按键（k）进行排序。你可以传入一个自定义的排序函数，它接受键值对（k, v）并返回一个用
    # 于排序的优先级值。
    # init_dict: 用于初始化字典的内容，默认是 None，即空字典。如果传入的是一个字典，将其转换为键值对的元组列表。
    # reverse: 一个布尔值，决定排序时是升序还是降序，默认为 False（升序）。
   #  self.sorted_keys: 用于缓存排序后的键列表。如果排序被更新过，该缓存将被设为 None，以便下次重新排序。
    # self.heap: 用来存储字典键的“堆”，heapq 模块提供了一个最小堆实现，这里用堆来保持按排序规则的顺序。
    def __init__(self, sort_func=lambda k, v: k, init_dict=None, reverse=False):
        if init_dict is None:
            init_dict = []
        if isinstance(init_dict, dict):
            init_dict = init_dict.items()
        self.sort_func = sort_func
        self.sorted_keys = None
        self.reverse = reverse
        self.heap = []
        for k, v in init_dict:
            self[k] = v
    # __setitem__(self, key, value) 用来设置字典项。
    def __setitem__(self, key, value):
        # 如果键 key 已经存在，则更新该键的值，并通过 sort_func 更新该键的优先级（排序值）。然后，利用 heapq.heapify(
        # self.heap) 对堆进行重排序，以确保堆的顺序正确。
        if key in self:
            super().__setitem__(key, value)
            for i, (priority, k) in enumerate(self.heap):
                if k == key:
                    self.heap[i] = (self.sort_func(key, value), key)
                    heapq.heapify(self.heap)
                    break
            self.sorted_keys = None
       # 如果键 key 不存在，则直接插入该键值对，并把 (priority, key) 元组插入到堆中。
        # 每次修改后，self.sorted_keys 被设为 None，这表示缓存的排序结果已失效，下一次访问 keys() 或 items() 时会重新排序。
        else:
            super().__setitem__(key, value)
            heapq.heappush(self.heap, (self.sort_func(key, value), key))
            self.sorted_keys = None
    # __delitem__(self, key) 用来删除字典中的项。
    def __delitem__(self, key):
        super().__delitem__(key)
        for i, (priority, k) in enumerate(self.heap):
            if k == key:
                del self.heap[i]
                heapq.heapify(self.heap)
                break
        self.sorted_keys = None
    # keys(self) 返回字典的键列表。
    def keys(self):
         # 如果 self.sorted_keys 为 None（即字典的内容或排序被更改过），则通过 sorted(self.heap) 排序堆中的元素，排序的顺序由 revers
        # e 参数控制（如果 reverse=True，则降序排列）。
        # sorted(self.heap) 返回的是一个按优先级排序的列表，每个元素是一个 (priority, key) 元组，所以通过 [k for _, k in sorted(self.heap)] 
        # 提取出排序后的键。
        if self.sorted_keys is None:
            self.sorted_keys = [k for _, k in sorted(self.heap, reverse=self.reverse)]
        return self.sorted_keys
    # items(self) 返回字典的键值对列表。
    def items(self):
        # 如果 self.sorted_keys 为 None，同样通过 sorted(self.heap) 排序堆中的元素。
        # 排序后的键用于访问字典中的值，并生成一个包含键值对的列表。
        if self.sorted_keys is None:
            self.sorted_keys = [k for _, k in sorted(self.heap, reverse=self.reverse)]
        sorted_items = [(k, self[k]) for k in self.sorted_keys]
        return sorted_items
    # _update_heap(self, key) 是一个私有方法，用于更新堆中的优先级。
    def _update_heap(self, key):
        for i, (priority, k) in enumerate(self.heap):
            if k == key:
                new_priority = self.sort_func(key, self[key])
                if new_priority != priority:
                    self.heap[i] = (new_priority, key)
                    heapq.heapify(self.heap)
                    self.sorted_keys = None
                break
    # __iter__(self) 返回一个迭代器，允许通过 for 循环遍历字典中的键。
    def __iter__(self):
        return iter(self.keys())
   #  __repr__(self) 返回该字典对象的字符串表示。
    def __repr__(self):
        return f"{type(self).__name__}({dict(self)}, sort_func={self.sort_func.__name__}, reverse={self.reverse})"
