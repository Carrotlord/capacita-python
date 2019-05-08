import math

from builtin_function import BuiltinFunction
from exception import throw_exception

def import_math(env):
    def binomial_choose(n, k):
        if k < 0 or k > n:
            return 0
        result = 1
        for i in xrange(1, min(k, n - k) + 1):
            # Do not use
            # result *= (n + 1 - i) / i
            # since dividing by i before multiplying
            # by result may have rounding errors
            result = (result * (n + 1 - i)) / i
        return result
    env.assign('pi', math.pi)
    env.assign('e', math.e)
    env.assign('phi', 1.6180339887498948482)
    env.assign('infinity', float('inf'))
    env.assign('negativeInfinity', -float('inf'))
    env.assign('nan', float('nan'))
    env.assign('sqrt', BuiltinFunction('sqrt', ['x'], math.sqrt))
    env.assign('cbrt', BuiltinFunction('cbrt', ['x'], lambda x: x ** 0.3333333333333333333))
    env.assign('log', BuiltinFunction('log', ['x', 'b'], lambda x, b: math.log(x, b)))
    env.assign('ln', BuiltinFunction('ln', ['x'], lambda x: math.log(x)))
    env.assign('binomialChoose', BuiltinFunction('binomialChoose', ['n', 'k'], binomial_choose))

def import_functional(env):
    def compose(f, g):
        def h(x):
            return f.execute([g.execute([x], env)], env)
        return BuiltinFunction('h', ['x'], h)
    def map_prime(f, lst):
        return map(lambda x: f.execute([x], env), lst)
    def flip(f):
        return BuiltinFunction('g', ['x', 'y'], lambda x, y: f.execute([y, x], env))
    def fold_left(f, lst):
        if len(lst) == 2:
            return f.execute(lst, env)
        else:
            return f.execute([fold_left(f, lst[0:-1]), lst[-1]], env)
    def fold_right(f, lst):
        if len(lst) == 2:
            return f.execute(lst, env)
        else:
            return f.execute([lst[0], fold_right(f, lst[1:])], env)
    def any_prime(f, lst):
        for elem in lst:
            result = f.execute([elem], env)
            if result:
                return True
        return False
    def all_prime(f, lst):
        for elem in lst:
            result = f.execute([elem], env)
            if not result:
                return False
        return True
    env.assign('compose', BuiltinFunction('compose', ['f', 'g'], compose))
    env.assign('map', BuiltinFunction('map', ['f', 'lst'], map_prime))
    env.assign('flip', BuiltinFunction('flip', ['f'], flip))
    env.assign('foldLeft', BuiltinFunction('foldLeft', ['f', 'lst'], fold_left))
    env.assign('foldRight', BuiltinFunction('foldRight', ['f', 'lst'], fold_right))
    env.assign('any', BuiltinFunction('any', ['f', 'lst'], any_prime))
    env.assign('all', BuiltinFunction('all', ['f', 'lst'], all_prime))

def perform_import(library, env):
    library = library.strip()
    obj = None
    if ' into ' in library:
        pieces = library.split()
        library = pieces[0]
        obj = pieces[2]
        env.new_frame()
    if library == 'math':
        import_math(env)
    elif library == 'functional':
        import_functional(env)
    else:
        throw_exception('NoExistingLibrary', 'No library named {0}'.format(library))
    if obj is not None:
        frame = env.pop()
        env.assign(obj, frame)
