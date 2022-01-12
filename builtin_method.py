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
            if type(elem) is dict and '$eq' in elem:
                eq_method = elem['$eq']
                # TODO : if there is no $eq method, and the $notEq (not equals) method
                #        is defined, use the default definition $eq(a, b) = not $notEq(a, b)
                for i, item in enumerate(obj):
                    if eq_method.execute([item], env):
                        return i
                return None
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

def remove_radix_prefix(digits):
    """
    Removes the '0x' or '0b' prefix from a string of binary or hexadecimal digits.
    Preserves the leading negative sign, if there is any.
    """
    if digits.startswith('-'):
        # Negative sign
        return '-' + digits[3:]
    return digits[2:]

def to_unsigned_bits(integer):
    """
    If the integer is positive, return it as a string of binary digits.
    If the integer is negative, return its unsigned representation in binary by
    indicating that there is an infinite stream of 1 bits to the left of the value.
    
    e.g. 123   -> "1111011"
         (-2)  -> "...11111110"
         (-23) -> "...111111101001"
    """
    if integer >= 0:
        # Remove '0b' prefix
        return bin(integer)[2:]
    value = abs(integer)
    mask = 0xf
    while mask < value:
        mask = (mask << 4) | 0xf
    # Put at least 4 extra ones digits on the representation
    return '...1111' + bin(mask & integer)[2:]

def is_int(n):
    return type(n) in [int, long]

def check_radix(radix):
    if (not is_int(radix)) or radix < 2 or radix > 36:
        throw_exception('UnsupportedBase', 'Base must be between 2 and 36 inclusive')

def char_range(start, stop):
    start = ord(start)
    stop = ord(stop)
    return ''.join(map(chr, xrange(start, stop + 1)))

digits = char_range('0', '9') + char_range('a', 'z')

def to_base(i, radix):
    check_radix(radix)
    if i == 0:
        return '0'
    result = ''
    j = abs(i)
    while j > 0:
        last = j % radix
        result = digits[last] + result
        j /= radix
    if i < 0:
        return '-' + result
    return result

def get_digit(n, index, radix):
    check_radix(radix)
    n = abs(n)
    # Left-shift digits in an arbitrary base
    n /= radix ** index
    # Get last digit
    return n % radix

def set_digit(n, index, radix, new_digit):
    check_radix(radix)
    sign = -1 if n < 0 else 1
    n = abs(n)
    if (not is_int(new_digit)) or new_digit < 0 or new_digit >= radix:
        throw_exception('UnsupportedDigit', 'Digit must be between 0 and {0} inclusive'.format(radix - 1))
    prev_digit = get_digit(n, index, radix)
    scale = radix ** index
    prev_value = prev_digit * scale
    n -= prev_value
    n += new_digit * scale
    return sign * n

def shift_left(value, num_digits, base):
    if num_digits < 0:
        return shift_right(value, -num_digits, base)
    if base == 2:
        return value << num_digits
    return value * (base ** num_digits)

def shift_right(value, num_digits, base):
    if num_digits < 0:
        return shift_left(value, -num_digits, base)
    if base == 2:
        return value >> num_digits
    return value / (base ** num_digits)

def number_methods(obj, name, env):
    if name == 'next':
        return builtin_function.BuiltinFunction('constant', [], lambda: obj + 1)
    elif name == 'previous':
        return builtin_function.BuiltinFunction('constant', [], lambda: obj - 1)
    if type(obj) in [int, long]:
        if name == 'toChar':
            return builtin_function.BuiltinFunction('toChar', [], lambda: strtools.CapString(chr(obj), False))
        elif name == 'bitNot':
            return builtin_function.BuiltinFunction('bitNot', [], lambda: ~obj)
        elif name == 'bitAnd':
            return builtin_function.BuiltinFunction('bitAnd', ['n'], lambda n: obj & n)
        elif name == 'bitOr':
            return builtin_function.BuiltinFunction('bitOr', ['n'], lambda n: obj | n)
        elif name == 'bitXor':
            return builtin_function.BuiltinFunction('bitXor', ['n'], lambda n: obj ^ n)
        elif name == 'bitNand':
            return builtin_function.BuiltinFunction('bitNand', ['n'], lambda n: ~(obj & n))
        elif name == 'bitNor':
            return builtin_function.BuiltinFunction('bitNor', ['n'], lambda n: ~(obj | n))
        elif name == 'bitXnor':
            return builtin_function.BuiltinFunction('bitXnor', ['n'], lambda n: ~(obj ^ n))
        elif name == 'toBin':
            # The bin function will add '0b' to the beginning of the binary string, which should be removed
            return builtin_function.BuiltinFunction('toBin', [],
                                                    lambda: strtools.CapString(remove_radix_prefix(bin(obj)), False))
        elif name == 'toHex':
            # The hex function will add '0x' to the beginning of the hexadecimal string, which should be removed
            return builtin_function.BuiltinFunction('toHex', [],
                                                    lambda: strtools.CapString(remove_radix_prefix(hex(obj)), False))
        elif name == 'toUnsignedBits':
            return builtin_function.BuiltinFunction('toUnsignedBits', [],
                                                    lambda: strtools.CapString(to_unsigned_bits(obj), False))
        elif name == 'getBit':
            return builtin_function.BuiltinFunction('getBit', ['i'], lambda i: (obj & (1 << i)) >> i)
        elif name == 'setBit':
            return builtin_function.BuiltinFunction('setBit', ['i'], lambda i: obj | (1 << i))
        elif name == 'resetBit':
            return builtin_function.BuiltinFunction('resetBit', ['i'], lambda i: obj & ~(1 << i))
        elif name == 'toggleBit':
            return builtin_function.BuiltinFunction('toggleBit', ['i'], lambda i: obj ^ (1 << i))
        elif name == 'toBase':
            return builtin_function.BuiltinFunction('toBase', ['base'],
                                                    lambda base: strtools.CapString(to_base(obj, base), False))
        elif name == 'getDigit':
            return builtin_function.BuiltinFunction('getDigit', ['index', 'base?'],
                                                    lambda index, base=10: get_digit(obj, index, base))
        elif name == 'setDigit':
            return builtin_function.BuiltinFunction('setDigit', ['index', 'newDigit', 'base?'],
                                                    lambda index, new_digit, base=10: set_digit(obj, index, base, new_digit))
        elif name == 'shiftLeft':
            return builtin_function.BuiltinFunction('shiftLeft', ['numDigits', 'base?'],
                                                    lambda num_digits, base=2: shift_left(obj, num_digits, base))
        elif name == 'shiftRight':
            return builtin_function.BuiltinFunction('shiftRight', ['numDigits', 'base?'],
                                                    lambda num_digits, base=2: shift_right(obj, num_digits, base))
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
