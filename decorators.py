from itertools import count
from symtable import Function
import time

def timer(fn):
    def wrapper(*args, **kwargs):
        start = time.time()
        res = fn(*args, **kwargs)
        end = time.time()
        print(f'\t{fn.__name__} computed in {end-start}')
        return res
    
    return wrapper

class Counter:

    def startCount(self, fn):
        def wrapper(*args, **kwargs):
            self.total = len(args[0])
            self.count = 0
            return fn(*args, **kwargs)
        return wrapper

    def __init__(self, function):
        self.function = function
        self.count = 0
        self.total = 1
        self.function.startCount = Counter.startCount

    def __call__(self, *args, **kwargs):
        self.count +=1
        print(f'{self.count}/{self.total} : ', end='')
        return self.function(*args, **kwargs)
