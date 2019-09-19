import function
import console
import strtools
import builtin_function

def produce_indentation(indent_size):
    return ' ' * indent_size

def abbreviated_format(obj):
    if type(obj) is dict:
        if '$type' in obj:
            return '<object {0}>'.format(obj['$type'])
        else:
            return '<object Instance>'
    elif obj.__class__ in [function.Function, builtin_function.BuiltinFunction]:
        result = '<function {0}('.format(obj.name)
        if obj.args is None:
            return result + '...)>'
        elif len(obj.args) == 0:
            return result + ')>'
        for arg_name in obj.args:
            result += arg_name + ', '
        return result[:-2] + ')>'
    else:
        return str(console.literal(obj))

def pretty_format(obj, indent_size=0):
    lines = []
    indentation = produce_indentation(indent_size + 4)
    if type(obj) is dict:
        lines.append('Object{')
        sorted_keys = sorted(obj.keys())
        for key in sorted_keys:
            value = obj[key]
            lines.append('{0}{1}, {2}'.format(indentation, key, abbreviated_format(value)))
        lines.append('}')
    elif type(obj) is list:
        if len(obj) == 0:
            return '[]'
        lines.append('[')
        for elem in obj:
            line = '{0}{1},'.format(indentation, pretty_format(elem, indent_size + 4))
            # Adjust brace indentation
            if line.endswith('},'):
                line = line[:-2] + indentation + '},'
            lines.append(line)
        # Remove trailing comma of last line
        lines[-1] = lines[-1][:-1]
        lines.append(']')
    else:
        lines = [str(console.literal(obj))]
    return (produce_indentation(indent_size) + '\n').join(lines)

def pretty_print(obj):
    print pretty_format(obj)

def pretty_format_wrapper(obj):
    return strtools.wrap_string(pretty_format(obj))
