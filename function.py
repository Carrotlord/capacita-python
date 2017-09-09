import re

from control_flow import prepare_control_flow
from exception import throw_exception
from execution import execute_lines
from control_flow import find_next_end_else
from env import Environment

def name_of_function(defn):
    """
    Given a function definition, returns the name of the function.
    e.g. 'sub myFunc(x, y)' -> 'myFunc'
    """
    match_obj = re.match(r'sub ([A-Za-z_][A-Za-z_0-9]*)', defn)
    name = match_obj.group(1)
    return name

def args_of_function(defn):
    """
    Given a function definition, returns a list of the argument names
    of the function.
    e.g. 'sub myFunc(x, y)' -> ['x', 'y']
    """
    match_obj = re.match(r'.*\((.*)\)', defn)
    args = match_obj.group(1)
    if len(args) == 0:
        return []
    arg_list = [arg.strip() for arg in args.split(',')]
    return arg_list

def extract_functions(prgm):
    """
    Removes all function bodies from prgm and inserts
    the functions into a new environment frame.
    """
    lines = prgm.split('\n')
    lines = [line.strip() for line in lines]
    env = Environment()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('sub '):
            name = name_of_function(line)
            arg_list = args_of_function(line)
            _, end = find_next_end_else(lines, i + 1, True)
            func_body = lines[i+1 : end]
            env.assign(name, Function(name, arg_list, func_body))
            # Remove the function definition from the program.
            lines[i : end+1] = []
        else:
            i += 1
    prgm = '\n'.join(lines)
    return prgm, env

class Function(object):
    """
    Implements a callable Capacita function.
    """
    def __init__(self, name, args, lines, supplied_env=None):
        """
        Initializes function object.
        lines are the lines of the function body
        prior to control flow being prepared.
        """
        self.name = name
        self.args = args
        prgm = '\n'.join(lines)
        prgm, self.defined_funcs = extract_functions(prgm)
        lines = prgm.split('\n')
        # All functions should return something,
        # which is null for 'void' functions.
        self.lines = prepare_control_flow(lines) + ['return null']
        self.supplied_env = supplied_env
        
    def execute(self, arg_values, env):
        """
        Executes this function's code, given argument values
        and an environment. Returns the result of the function.
        """
        if len(self.args) != len(arg_values):
            throw_exception('ArgValueException',
                            'Number of arguments does not match function definition')
        if self.supplied_env is not None:
            env = self.supplied_env
        env.new_frame()
        env.merge_latest(self.defined_funcs)
        i = 0
        # Put function arguments into environment frame:
        while i < len(self.args):
            current_arg = self.args[i]
            current_val = arg_values[i]
            env.assign(current_arg, current_val)
            i += 1
        result = execute_lines(self.lines, env)
        # Remove the stack frame created by this function:
        env.pop()
        return result
    
    def supply(self, env):
        """
        Gives a higher-order function a special environment.
        This provides a copy of the current function, updated
        with the correct environment.
        """
        new_func = Function(self.name, self.args, [], env.copy())
        new_func.lines = self.lines
        new_func.defined_funcs = self.defined_funcs
        return new_func
        
    def __repr__(self):
        return '<function ' + self.name + '(' + str(self.args)[1:-1] + \
               ') -> ' + str(tuple(self.lines)) + '>'
    
    def __str__(self):
        return repr(self)
