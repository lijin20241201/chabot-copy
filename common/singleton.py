# 在这个装饰器中，cls 是传入的类（即类本身，而不是它的实例）。装饰器的目的是确保该类只有一个实例（即单例模式）。
# singleton 是一个装饰器函数，它接收一个类 cls 作为参数。
# 在 Python 中，装饰器是一个函数，它接收一个函数或类作为参数，并返回一个修改后的版本。你的 singleton 方法就是一个典型的装饰器，专门用于确
# 保类只会有一个实例（即单例模式）。
# 为什么 singleton 是一个装饰器？
# 接受类作为参数： singleton 装饰器接受一个类 cls 作为参数。装饰器的目标是修改这个类，使它在整个程序中只有一个实例。
# 返回一个函数： 装饰器需要返回一个新的函数或类。在你的代码中，singleton 返回了 get_instance 函数，这个函数实现了单例模式的逻辑。
# 替换原始类： 使用装饰器后，原本定义的类会被 get_instance 函数替代。因此，每次访问这个类时，实际是通过 get_instance 来创建实例，
# 而 get_instance 会保证每次返回的是同一个实例。
# 装饰器 @singleton 会替换原始类定义，使得类变成一个单例。
def singleton(cls):
    instances = {}
    def get_instance(*args, **kwargs):
        # 在 get_instance 函数内部，首先检查该类是否已经存在于 instances 字典中。如果没有，创建该类的实例并将其存储在字典中。
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        # 如果该类已经有实例，则直接返回该实例。
        # 这种做法确保了每次调用 get_instance 时，返回的都是同一个实例。
        return instances[cls]
    return get_instance
