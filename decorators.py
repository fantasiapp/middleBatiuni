import time

def timer(f):
    def wrapper(*args, **kwargs):
        start = time.time()
        res = f(*args, **kwargs)
        end = time.time()
        print(f'\t{f.__name__} computed in {end-start}')
        return res
    
    return wrapper