import re

from control_flow import prepare_control_flow
from exception import throw_exception
from execution import execute_lines
from control_flow import find_next_end_else
from env import Environment

def name_of_function(defn):
    """
    """
    match_obj = re.match(r'sub ([A-Za-z_][A-Za-z_0-9]*)', defn)
    name = match_obj.group(1)
    return name

def args_of_function(defn):
    """
    """
    match_obj = re.match(r'.*\((.*)\)', defn)
    args = match_obj.group(1)
    if len(args) == 0:
        return []
    arg_list = [arg.strip() for arg in args.split(',')]
    return arg_list

def extract_functions(prgm):
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
    def __init__(self, name, args, lines):
        """
        Initializes function object.
        lines are the lines of the function body
        prior to control flow being prepared.
        """
        self.name = name
        self.args = args
        # All functions should return something,
        # which is null for 'void' functions.
        self.lines = prepare_control_flow(lines) + ['return null']
        
    def execute(self, arg_values, env):
        if len(self.args) != len(arg_values):
            throw_exception('ArgValueException',
                            'Number of arguments does not match function definition')
        env.new_frame()
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
        
    def __repr__(self):
        return '<' + self.name + '(' + str(self.args)[1:-1] + ') -> ' + str(self.lines) + '>'
    
    def __str__(self):
        return repr(self)
