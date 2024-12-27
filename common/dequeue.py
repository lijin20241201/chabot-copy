from queue import Full, Queue
from time import monotonic as time


# 这段代码定义了一个自定义的队列类 Dequeue，它是 Python 标准 Queue 类的子类。Dequeue 类扩展了 Queue，实现了在队列的
# 左边 插入元素的功能，而标准 Queue 并不支持这一操作。Queue 类提供了线程安全的 FIFO（先进先出）队列操作。
# 通过继承 Queue，Dequeue 类继承了所有基本的队列功能（如 put()、get() 等），同时还可以在队列的左边插入元素，这是标准 Queue 不支持的功能。
# 和 Queue 类一样，Dequeue 类通过条件变量（not_full 和 not_empty）确保队列操作是线程安全的。这意味着多个线程可以安全地同时对队列进行操作
# 而不会出现数据冲突或状态错误。
class Dequeue(Queue):
    # putleft 是一个自定义方法，用于将一个元素插入到队列的左端。item: 要加入队列的元素。
    # block: 是否阻塞（即等待）当队列已满时。如果为 True，则会等待直到队列有空闲位置；如果为 False，则直接抛出 Full 异常。
    # timeout: 如果阻塞（block=True），则表示等待的最大时间（秒）。如果在 timeout 时间内队列没有空间，则抛出 Full 异常。
    def putleft(self, item, block=True, timeout=None):
        # not_full 是一个条件变量，用于同步对队列的访问，避免多个线程同时操作队列导致冲突。如果队列满了，操作线程会在此处等待。
        with self.not_full:
            # 如果不阻塞（block=False），方法会检查队列的当前大小 (_qsize()) 是否大于等于最大容量 (maxsize)。如果队列已满，直接抛出 Full 异常。
            if self.maxsize > 0:
                if not block:
                    if self._qsize() >= self.maxsize:
                        raise Full
                # 如果阻塞，并且没有指定 timeout，方法会持续检查队列大小，并在队列已满时调用 self.not_full.wait() 进行等待，直到队列有空闲位置。
                elif timeout is None:
                    while self._qsize() >= self.maxsize:
                        self.not_full.wait()
                elif timeout < 0:
                    raise ValueError("'timeout' must be a non-negative number")
               #  如果指定了 timeout，方法会计算剩余的等待时间，并在此时间内继续等待。如果在 timeout 时间内队列仍然满，则抛出 Full 异常。
                else:
                    endtime = time() + timeout
                    while self._qsize() >= self.maxsize:
                        remaining = endtime - time()
                        if remaining <= 0.0:
                            raise Full
                        self.not_full.wait(remaining)
            # 如果队列有空间或者不需要等待，putleft 方法会调用 _putleft 方法将元素插入队列的左端。
            self._putleft(item)
            # unfinished_tasks 变量记录未完成任务的数量，每当有新元素插入时，任务数加一。self.not_empty.notify() 用于
            # 通知其他可能在 get() 上等待的线程，表示队列现在不为空，可能有元素可以被处理。
            self.unfinished_tasks += 1
            self.not_empty.notify()
    # putleft_nowait 方法是 putleft 的快捷方式，默认设置 block=False，即不阻塞。如果队列已满，直接抛出
    # Full 异常，而不会等待空间。
    def putleft_nowait(self, item):
        return self.putleft(item, block=False)
    # _putleft 是一个内部方法，负责将元素插入到队列的左端。这里使用了 deque（双端队列）来实现队列，deque 支持在
    # 两端进行高效的插入和删除。appendleft 方法会把元素添加到队列的左端。
    def _putleft(self, item):
        self.queue.appendleft(item)
