import sys
import strtools

from table import Table

import type_tree

def display(obj, use_newline=True):
    """
    Implementation of print functionality. Strings will not be printed with
    surrounding quotes, while other objects are printed as-is.
    """
    if obj.__class__ is strtools.CapString:
        if use_newline:
            print(obj.contents)
        else:
            sys.stdout.write(obj.contents)
    else:
        if use_newline:
            print(literal(obj))
        else:
            sys.stdout.write(str(literal(obj)))

def filter_attributes(obj):
    # Do not keep the value of the 'this' pointer
    return {k: v for k, v in obj.items() if k != 'this'}

def obj_to_str(obj):
    representation = 'Object{'
    i = 0
    filtered = filter_attributes(obj)
    for key, value in filtered.items():
        representation += '#' + key + ', '
        if value is obj:
            representation += '...'
        else:
            representation += str(literal(value))
        if i != len(filtered) - 1:
            representation += ' | '
        i += 1
    return representation + '}'

def list_to_str(lst):
    representation = '['
    i = 0
    for elem in lst:
        if elem is lst:
            representation += '...'
        else:
            representation += str(literal(elem))
        if i != len(lst) - 1:
            representation += ', '
        i += 1
    return representation + ']'

def table_to_str(table):
    representation = '{'
    i = 0
    keys = table.keys()
    for key in keys:
        if key is table:
            representation += '...'
        else:
            representation += str(literal(key))
        representation += ', '
        value = table.get(key)
        if value is table:
            representation += '...'
        else:
            representation += str(literal(value))
        if i != len(keys) - 1:
            representation += ' | '
        i += 1
    return representation + '}'
        
def literal(obj):
    """
    Returns a string representation of the object as a Capacita literal.
    Similiar to Python's repr(...) function.
    """
    if obj is True:
        return 'true'
    elif obj is False:
        return 'false'
    elif obj is None:
        return 'null'
    elif type(obj) is dict:
        # This is a user-created object
        return obj_to_str(obj)
    elif type(obj) is list:
        return list_to_str(obj)
    elif obj.__class__ is Table:
        return table_to_str(obj)
    elif obj.__class__ is strtools.CapString:
        return '"{0}"'.format(strtools.unescape(obj.contents))
    elif obj.__class__ is type_tree.TypeTree:
        return '<type {0}>'.format(obj.get_default_name())
    else:
        return obj
