import sys

def display(obj, use_newline=True):
    """
    Implementation of print functionality. Strings will not be printed with
    surrounding quotes, while other objects are printed as-is.
    """
    if type(obj) is str and len(obj) >= 2 and obj[0] == '"' and obj[-1] == '"':
        if use_newline:
            print(obj[1:-1])
        else:
            sys.stdout.write(obj[1:-1])
    else:
        if use_newline:
            print(literal(obj))
        else:
            sys.stdout.write(str(literal(obj)))
        
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
    else:
        return obj
