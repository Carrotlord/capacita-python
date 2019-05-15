from exception import throw_exception

class BuiltinFunction(object):
    def __init__(self, name, args, action, supplied_env=None):
        self.name = name
        self.args = args
        self.action = action
        self.supplied_env = supplied_env

    def get_num_args(self):
        return len(self.args)
        
    def execute(self, arg_values, env=None):
        if self.args is not None and len(arg_values) != len(self.args):
            throw_exception('IncorrectNumberOfArguments',
                            'Wrong number of arguments passed to built-in function')
        return self.action(*arg_values)
        
    def supply(self, env):
        # A supplied environment has no meaning for a built-in function:
        pass
        
    def __repr__(self):
        return '<function ' + self.name + '(' + str(self.args)[1:-1] + ')>'
        
    def __str__(self):
        return repr(self)

def int_div_action(a, b):
    """
    Returns a/b, discarding any remainder.
    """
    return int(a) / int(b)

def make_list_action(*args):
    """
    Returns a list containing the given arguments.
    """
    return list(args)

int_div = BuiltinFunction('intDiv', ['a', 'b'], int_div_action)
make_list = BuiltinFunction('makeList', None, make_list_action)
