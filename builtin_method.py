import re
import execution
import type_restrict
import type_tree

from builtin_function import BuiltinFunction
from table import Table
from exception import throw_exception

# None is used as a return value to indicate that no corresponding method was found
# for the name.

def list_methods(obj, name, env):
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
        return BuiltinFunction('list', ['newElem'], func_push)
    elif name == 'removeAt':
        return BuiltinFunction('constant', ['index'], lambda i: obj.pop(i))
    elif name == 'insertAt':
        def insert_at(index, elem):
            obj.insert(index, elem)
            return obj
        return BuiltinFunction('insertAt', ['index', 'elem'], insert_at)
    elif name == 'reverse':
        def reverse_list():
            obj.reverse()
            return obj
        return BuiltinFunction('reverse', [], reverse_list)
    elif name == 'find':
        # Returns the position of the element in the list.
        # If the element is not found, returns null.
        def find(elem):
            try:
                return obj.index(elem)
            except ValueError:
                return None
        return BuiltinFunction('find', ['elem'], find)
    return None

def obj_methods(obj, name, env):
    # This is a method call
    if obj[name].__class__ is BuiltinFunction:
        # Built in functions don't need a this pointer
        return obj[name]
    else:
        env.new_this(obj)
        method = obj[name]
        method.activate_method()
        return method
    return None

def number_methods(obj, name, env):
    if name == 'next':
        return BuiltinFunction('constant', [], lambda: obj + 1)
    elif name == 'previous':
        return BuiltinFunction('constant', [], lambda: obj - 1)
    return None

def table_methods(obj, name, env):
    if name == 'length' or name == 'size':
        return BuiltinFunction('constant', [], lambda: len(obj))
    elif name == 'keys':
        return BuiltinFunction('constant', [], lambda: obj.keys())
    elif name == 'hasKey':
        return BuiltinFunction('hasKey', ['key'], lambda key: obj.has_key(key))
    return None

def type_tree_methods(obj, name, env):
    # This method allows us to view the type tree of a given environment
    if name == 'format':
        return BuiltinFunction('constant', [], lambda: obj.format_as_literal())
    return None

def dot_operator(obj, name, env):
    if type(obj) is str and re.match(r'\$?[A-Za-z_][A-Za-z_0-9]*', obj):
        obj = env.get(obj)
    obj = execution.convert_value(obj, env)
    method = None
    if type_restrict.is_considered_list(obj):
        method = list_methods(obj, name, env)
    elif type(obj) is dict:
        method = obj_methods(obj, name, env)
    elif type(obj) in [int, long, float]:
        method = number_methods(obj, name, env)
    elif obj.__class__ is Table:
        method = table_methods(obj, name, env)
    elif obj.__class__ is type_tree.TypeTree:
        method = type_tree_methods(obj, name, env)
    if method is None:
        throw_exception('NoSuchAttribute', str(obj) + ' object has no attribute ' + name)
    else:
        return method
