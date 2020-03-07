import re
import execution
import type_restrict
import type_tree

from table import Table
from exception import throw_exception

import builtin_function
import strtools

# None is used as a return value to indicate that no corresponding method was found
# for the name.

def list_methods(obj, name, env):
    if name == 'length' or name == 'size':
        length = len(obj)
        return builtin_function.BuiltinFunction('constant', [], lambda: length)
    elif name == 'pop':
        last_elem = obj.pop()
        return builtin_function.BuiltinFunction('constant', [], lambda: last_elem)
    elif name == 'push':
        def func_push(new_elem):
            obj.append(new_elem)
            return obj
        return builtin_function.BuiltinFunction('list', ['newElem'], func_push)
    elif name == 'removeAt':
        return builtin_function.BuiltinFunction('constant', ['index'], lambda i: obj.pop(i))
    elif name == 'insertAt':
        def insert_at(index, elem):
            obj.insert(index, elem)
            return obj
        return builtin_function.BuiltinFunction('insertAt', ['index', 'elem'], insert_at)
    elif name == 'reverse':
        def reverse_list():
            obj.reverse()
            return obj
        return builtin_function.BuiltinFunction('reverse', [], reverse_list)
    elif name == 'find':
        # Returns the position of the element in the list.
        # If the element is not found, returns null.
        def find(elem):
            try:
                return obj.index(elem)
            except ValueError:
                return None
        return builtin_function.BuiltinFunction('find', ['elem'], find)
    elif name == 'slice':
        def slice(start, stop=None):
            if stop is None:
                return obj[start:]
            else:
                return obj[start:stop]
        return builtin_function.BuiltinFunction('slice', ['start', 'stop?'], slice)
    return None

def str_methods(obj, name, env):
    if name == 'length' or name == 'size':
        # Strings are immutable, so only call len() once
        length = len(obj)
        return builtin_function.BuiltinFunction('constant', [], lambda: length)
    elif name == 'ord' or name == 'charNum':
        def char_num(string):
            if len(string) == 0:
                throw_exception(
                    'StringEmpty',
                    'Cannot convert first character to integer when string is empty'
                )
            return ord(string[0])
        return builtin_function.BuiltinFunction('charNum', [], lambda: char_num(obj))
    elif name == 'charAt':
        return builtin_function.BuiltinFunction('charAt', ['i'], lambda i: strtools.index_string(obj, i))
    elif name == 'insertAt':
        def insert_at(index, substr):
            strtools.validate_string_index(obj, index)
            return strtools.CapString(obj.contents[0:index] + substr.contents + obj.contents[index:], False)
        return builtin_function.BuiltinFunction('insertAt', ['index', 'substr'], insert_at)
    elif name == '$internals':
        # View internals of a string, for debugging purposes.
        print(repr(obj))
        return builtin_function.BuiltinFunction('constant', [], lambda: None)
    elif name == 'slice':
        def slice_string(start, stop=None):
            strtools.validate_string_index(obj, start)
            if stop is not None:
                strtools.validate_string_index(obj, stop)
                return strtools.CapString(obj.contents[start:stop], False)
            else:
                return strtools.CapString(obj.contents[start:], False)
        return builtin_function.BuiltinFunction('slice', ['start', 'stop?'], slice_string)
    elif name == 'replaceSlice':
        def replace_slice(start, stop, substr):
            strtools.validate_string_index(obj, start)
            strtools.validate_string_index(obj, stop)
            return strtools.CapString(obj.contents[0:start] + substr.contents + obj.contents[stop:])
        return builtin_function.BuiltinFunction('replaceSlice', ['start', 'stop', 'substr'], replace_slice)
    contents = obj.contents
    if name == 'split':
        def split_string(separator=None):
            if separator is None:
                return [strtools.CapString(elem, False) for elem in contents.split()]
            else:
                separator = separator.contents
                return [strtools.CapString(elem, False) for elem in contents.split(separator)]
        return builtin_function.BuiltinFunction('split', ['separator?'], split_string)
    elif name == 'find':
        def find_in_string(string, substr):
            result = string.find(substr)
            if result == -1:
                return None
            return result
        return builtin_function.BuiltinFunction('find', ['substring'], lambda s: find_in_string(contents, s.contents))
    return None

def obj_methods(obj, name, env):
    # This is a method call
    if obj[name].__class__ is builtin_function.BuiltinFunction:
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
        return builtin_function.BuiltinFunction('constant', [], lambda: obj + 1)
    elif name == 'previous':
        return builtin_function.BuiltinFunction('constant', [], lambda: obj - 1)
    if type(obj) in [int, long] and name == 'toChar':
        return builtin_function.BuiltinFunction('toChar', [], lambda: strtools.CapString(chr(obj), False))
    return None

def table_methods(obj, name, env):
    if name == 'length' or name == 'size':
        return builtin_function.BuiltinFunction('constant', [], lambda: len(obj))
    elif name == 'keys':
        return builtin_function.BuiltinFunction('constant', [], lambda: obj.keys())
    elif name == 'hasKey':
        return builtin_function.BuiltinFunction('hasKey', ['key'], lambda key: obj.has_key(key))
    return None

def type_tree_methods(obj, name, env):
    # This method allows us to view the type tree of a given environment
    if name == 'format':
        return builtin_function.BuiltinFunction('constant', [], lambda: obj.format_as_literal())
    return None

def dot_operator(obj, name, env):
    if type(obj) is str and re.match(r'\$?[A-Za-z_][A-Za-z_0-9]*', obj):
        obj = env.get(obj)
    obj = execution.convert_value(obj, env)
    method = None
    if type_restrict.is_considered_list(obj):
        method = list_methods(obj, name, env)
    elif obj.__class__ is strtools.CapString:
        method = str_methods(obj, name, env)
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
