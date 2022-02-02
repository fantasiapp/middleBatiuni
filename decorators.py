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

def apiCall(fn):
    '''
        Add status code, and default warning, OK, and error message.
        Could enhance the handling of different warning cases.
    '''
    def wrapper(*args, **kwargs):
        try:
            res = fn(*args, **kwargs)
            if not res:
                return {fn.__name__: 'warning',
                        'message': fn.__name__ + ' : No result found.'
                        }
            else:
                res.update({
                    fn.__name__: 'OK',
                    'message': 'Oll Korrekt.'
                    })
                return res
        except:
            return {fn.__name__: 'error',
                    'message': ' : An unexpecteed error occured.'
                    }
    return wrapper