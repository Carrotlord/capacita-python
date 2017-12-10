from builtin_function import BuiltinFunction
from exception import throw_exception

import re

def dot_operator(obj, name, env):
    if type(obj) is str and re.match(r'\$?[A-Za-z_][A-Za-z_0-9]*', obj):
        obj = env.get(obj)
    if type(obj) is list:
        if name == 'length' or name == 'size':
            length = len(obj)
            return BuiltinFunction('constant', [], lambda: length)
        elif name == 'pop':
            last_elem = obj.pop()
            return BuiltinFunction('constant', [], lambda: last_elem)
        elif name == 'push':
            def func_push(new_elem):
                obj.append(new_elem)
                return obj
            return BuiltinFunction('list', ['new_elem'], func_push)
    elif type(obj) is dict:
        env.new_this(obj)
        return obj[name]
    throw_exception('NoSuchAttribute', str(obj) + ' object has no attribute ' + name)
