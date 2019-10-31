import math

from exception import throw_exception

import builtin_function
import capacita
import pretty_print

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
    def fib(n):
        # Use the matrix form of Fibonacci numbers
        # to perform the computation in O(log(n)) operations.
        # Please see the Wikipedia page on Fibonacci numbers
        # for more information.
        if n == 0 or n == 1:
            return n
        def is_odd(n):
            return (n & 1) == 1
        if is_odd(n):
            k = (n + 1) / 2
            return fib(k) ** 2 + fib(k - 1) ** 2
        else:
            k = n / 2
            fib_k = fib(k)
            return 2 * fib(k - 1) * fib_k + fib_k ** 2
    def differentiate(f, dx=1e-6):
        def f_prime(x):
            df = f.execute([x + dx], env) - f.execute([x], env)
            return df / dx
        return builtin_function.BuiltinFunction('fPrime', ['x'], f_prime)
    def integrate(f, a, b, num_rectangles=1000):
        if b < a:
            return -integrate(f, b, a, num_rectangles)
        current_sum = 0
        dx = (b - a) / float(num_rectangles)
        while a < b:
            current_sum += f.execute([a], env) * dx
            a += dx
        return current_sum
    env.assign('pi', math.pi)
    env.assign('e', math.e)
    env.assign('phi', 1.6180339887498948482)
    env.assign('infinity', float('inf'))
    env.assign('negativeInfinity', -float('inf'))
    env.assign('nan', float('nan'))
    env.assign('sqrt', builtin_function.BuiltinFunction('sqrt', ['x'], math.sqrt))
    env.assign('cbrt', builtin_function.BuiltinFunction('cbrt', ['x'], lambda x: x ** 0.3333333333333333333))
    env.assign('log', builtin_function.BuiltinFunction('log', ['x', 'b'], lambda x, b: math.log(x, b)))
    env.assign('ln', builtin_function.BuiltinFunction('ln', ['x'], lambda x: math.log(x)))
    env.assign('binomialChoose', builtin_function.BuiltinFunction('binomialChoose', ['n', 'k'], binomial_choose))
    env.assign('fib', builtin_function.BuiltinFunction('fib', ['n'], fib))
    env.assign('factorial', builtin_function.BuiltinFunction('factorial', ['n'], math.factorial))
    env.assign('differentiate', builtin_function.BuiltinFunction('differentiate', ['f', 'epsilon?'], differentiate))
    env.assign('min', builtin_function.BuiltinFunction('min', ['n', '[args]'], min))
    env.assign('max', builtin_function.BuiltinFunction('max', ['n', '[args]'], max))
    env.assign('integrate', builtin_function.BuiltinFunction('integrate', ['f', 'a', 'b', 'numRectangles?'], integrate))
    env.assign('sin', builtin_function.BuiltinFunction('sin', ['x'], math.sin))
    env.assign('cos', builtin_function.BuiltinFunction('cos', ['x'], math.cos))
    env.assign('atan', builtin_function.BuiltinFunction('atan', ['x'], math.atan))
    env.assign('atan2', builtin_function.BuiltinFunction('atan2', ['y', 'x'], math.atan2))

def import_functional(env):
    def compose(f, g):
        def h(x):
            return f.execute([g.execute([x], env)], env)
        return builtin_function.BuiltinFunction('h', ['x'], h)
    def map_prime(f, lst):
        return map(lambda x: f.execute([x], env), lst)
    def filter_prime(predicate, lst):
        return filter(lambda x: predicate.execute([x], env), lst)
    def flip(f):
        return builtin_function.BuiltinFunction('g', ['x', 'y'], lambda x, y: f.execute([y, x], env))
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
    def curry(f):
        num_args = f.get_num_args()
        if num_args <= 1:
            return f
        else:
            def curried_f(x):
                partially_applied_f = partial(f, [x])
                return curry(partially_applied_f)
            return builtin_function.BuiltinFunction('g', ['x'], curried_f)
    def partial(f, fixed_args):
        num_original_args = f.get_num_args()
        num_fixed_args = len(fixed_args)
        num_args_needed = num_original_args - num_fixed_args
        if num_args_needed < 0:
            throw_exception('TooManyFixedArguments',
                'Function {0} requires {1} arguments, but passing in {2}'.format(
                    f.name, num_original_args, num_fixed_args
                )
            )
        arg_names = ['x' + str(i) for i in xrange(num_args_needed)]
        def partially_applied_f(*args):
            return f.execute(fixed_args + list(args), env)
        return builtin_function.BuiltinFunction('fPrime', arg_names, partially_applied_f)
    env.assign('compose', builtin_function.BuiltinFunction('compose', ['f', 'g'], compose))
    env.assign('map', builtin_function.BuiltinFunction('map', ['f', 'lst'], map_prime))
    env.assign('filter', builtin_function.BuiltinFunction('filter', ['predicate', 'lst'], filter_prime))
    env.assign('flip', builtin_function.BuiltinFunction('flip', ['f'], flip))
    env.assign('foldLeft', builtin_function.BuiltinFunction('foldLeft', ['f', 'lst'], fold_left))
    env.assign('foldRight', builtin_function.BuiltinFunction('foldRight', ['f', 'lst'], fold_right))
    env.assign('any', builtin_function.BuiltinFunction('any', ['f', 'lst'], any_prime))
    env.assign('all', builtin_function.BuiltinFunction('all', ['f', 'lst'], all_prime))
    env.assign('curry', builtin_function.BuiltinFunction('curry', ['f'], curry))
    env.assign('partial', builtin_function.BuiltinFunction('partial', ['f', 'fixedArgs'], partial))

def import_debugging(env):
    env.assign('getFrames', builtin_function.BuiltinFunction('getFrames', [], lambda: env.frames))
    env.assign('getThisFrames', builtin_function.BuiltinFunction('getThisFrames', [], lambda: env.this_pointers))
    env.assign('repl', builtin_function.BuiltinFunction('repl', [], lambda: capacita.repl(env)))

def import_pretty_print(env):
    env.assign('prettyFormat', builtin_function.BuiltinFunction('prettyFormat', ['obj'], pretty_print.pretty_format_wrapper))
    env.assign('prettyPrint', builtin_function.BuiltinFunction('prettyPrint', ['obj'], pretty_print.pretty_print))

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
    elif library == 'debugging':
        import_debugging(env)
    elif library == 'prettyPrint':
        import_pretty_print(env)
    elif library.startswith('"') and library.endswith('"'):
        # Import a program from the file system
        capacita.execute_file(library[1:-1], env)
    else:
        throw_exception('NoExistingLibrary', 'No library named {0}'.format(library))
    if obj is not None:
        frame = env.pop()
        env.assign(obj, frame)
