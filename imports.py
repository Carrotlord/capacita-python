import math

from builtin_function import BuiltinFunction

def import_math(env):
    env.assign('pi', math.pi)
    env.assign('e', math.e)
    env.assign('phi', 1.6180339887498948482)
    env.assign('sqrt', BuiltinFunction('sqrt', ['x'], math.sqrt))
    env.assign('cbrt', BuiltinFunction('cbrt', ['x'], lambda x: x ** 0.3333333333333333333))
    env.assign('log', BuiltinFunction('log', ['x', 'b'], lambda x, b: math.log(x, b)))
    env.assign('ln', BuiltinFunction('ln', ['x'], lambda x: math.log(x)))

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
    if obj is not None:
        frame = env.pop()
        env.assign(obj, frame)
