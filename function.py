import re

from prepare_program import prepare_program
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
    max_len = len(lines)
    while i < max_len:
        line = lines[i]
        # Transform classes into functions that return objects
        if line.startswith('class '):
            match_obj = re.match(r'class ([\$A-Za-z_][A-Za-z0-9_]*)\((.*)\)(.*)', line)
            child_class_name = match_obj.group(1)
            arguments = match_obj.group(2)
            parent_classes = match_obj.group(3)
            inherit_obj = re.match(r' inherits (.*)', parent_classes)
            if inherit_obj:
                parent_class_names = inherit_obj.group(1)
                classes = [name.strip() for name in parent_class_names.split(',')]
                env.new_type(classes, child_class_name)
            else:
                # There were no parent classes provided.
                # By default, this class should inherit from Object.
                env.new_type(['Object'], child_class_name)
            lines[i] = 'sub ' + child_class_name + '(' + arguments + ')'
            lines.insert(i + 1, '$type="' + child_class_name + '"')
            max_len += 1
            _, end = find_next_end_else(lines, i + 1, True)
            lines.insert(end, 'return this')
            max_len += 1
        i += 1
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
        # All functions should return something,
        # which is null for 'void' functions.
        self.lines = prepare_program(prgm) + ['return null']
        self.supplied_env = supplied_env
        self.is_method = False
    
    def activate_method(self):
        self.is_method = True
        
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
        # Remove the last this pointer:
        if self.is_method:
            env.pop_this()
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
