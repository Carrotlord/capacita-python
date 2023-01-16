import re

from exception import throw_exception
from control_flow import find_next_end_else

import execution
import env as environment
import arguments
import prepare_program
import line_manager
import builtin_function

def is_function(obj):
    obj_class = obj.__class__
    return obj_class is Function or obj_class is builtin_function.BuiltinFunction

def extract_data(defn, kind):
    match_obj = re.match(r'sub ([A-Za-z_][A-Za-z_0-9]* )?(\$?[A-Za-z_][A-Za-z_0-9]*)', defn)
    if kind == 'return_type':
        kind = match_obj.group(1)
        if kind is not None:
            return kind.strip()
    elif kind == 'func_name':
        return match_obj.group(2)
    return None

def name_of_function(defn):
    """
    Given a function definition, returns the name of the function.
    e.g. 'sub myFunc(x, y)' -> 'myFunc'
    """
    return extract_data(defn, 'func_name')

def return_type_of_function(defn):
    return extract_data(defn, 'return_type')

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

def define_single_line_function(contents, executing_constructor, env):
    # TODO : allow default arguments in function definition
    split_index = contents.find('=')
    header = contents[0:split_index]
    body = contents[split_index + 1:]
    header = 'sub ' + header
    body = 'return ' + body
    name = name_of_function(header)
    arg_list = args_of_function(header)
    ret_type = return_type_of_function(header)
    new_function = Function(name, arg_list, [body], return_type=ret_type)
    if executing_constructor:
        # Mark this function as a method
        new_function.defined_as_method = True
    env.assign(name, new_function)
    # Save this single line function as a hook, which
    # is important for knowing which functions require a
    # supplied environment.
    env.assign_hook(name, new_function)

def extract_functions(prgm, existing_env=None):
    """
    Removes all function bodies from prgm and inserts
    the functions into a new environment frame.
    """
    is_line_mgr_given = False
    if type(prgm) is str:
        lines = prgm.split('\n')
    elif type(prgm) is list:
        # We are already given a list of lines
        lines = prgm
    else:
        is_line_mgr_given = True
    if is_line_mgr_given:
        # We are already given a line manager
        line_mgr = prgm
    else:
        lines = [line.strip() for line in lines]
        line_mgr = line_manager.LineManager(lines)
    line_mgr = prepare_program.lift_lambdas(line_mgr)
    prepare_program.replace_op_overload_syntax(line_mgr)
    if existing_env is None:
        env = environment.Environment()
    else:
        env = existing_env
    i = 0
    max_len = len(line_mgr)
    while i < max_len:
        line = line_mgr[i]
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
            line_mgr[i] = 'sub ' + child_class_name + '(' + arguments + ')'
            line_mgr.insert(i + 1, '$type="' + child_class_name + '"')
            max_len += 1
            _, end = find_next_end_else(line_mgr, i + 1, True)
            line_mgr.insert(end, 'return this')
            max_len += 1
        i += 1
    i = 0
    hooks_reference = None
    while i < len(line_mgr):
        line = line_mgr[i]
        if line.startswith('sub '):
            name = name_of_function(line)
            arg_list = args_of_function(line)
            ret_type = return_type_of_function(line)
            _, end = find_next_end_else(line_mgr, i + 1, True)
            func_body = line_mgr.subset(i + 1, end)
            hooks_reference = env.assign_hook(name, Function(name, arg_list, func_body, return_type=ret_type))
            # Remove the function definition from the program,
            # and replace it with a hook directive.
            line_mgr[i : end+1] = [':hook {0}'.format(name)]
        else:
            i += 1
    return line_mgr, env, hooks_reference

class Function(object):
    """
    Implements a callable Capacita function.
    """
    def __init__(self, name, args, line_mgr, supplied_env=None, return_type=None):
        """
        Initializes function object.
        lines are the lines of the function body
        prior to control flow being prepared.
        """
        self.name = name
        self.args = args
        self.return_type = return_type
        line_mgr, self.defined_funcs, self.hooks = extract_functions(line_mgr)
        self.line_mgr = line_mgr
        prepare_program.prepare_program(self.line_mgr)
        self.supplied_env = supplied_env
        self.called_as_method = False
        self.defined_as_method = False
        self.is_constructor = self.check_is_constructor()

    def check_is_constructor(self):
        """
        Returns True if this function is a constructor, else False.
        """
        # A function is a constructor if it defines its
        # own type on the first line of the function body.
        if len(self.line_mgr) == 0:
            return False
        return self.line_mgr[0].startswith('$type=')

    def get_num_args(self):
        return len(self.args)

    def activate_method(self):
        self.called_as_method = True
        
    def execute(self, arg_values, env):
        """
        Executes this function's code, given argument values
        and an environment. Returns the result of the function.
        """
        if self.supplied_env is not None:
            env = self.supplied_env
        env.new_frame()
        env.merge_latest(self.defined_funcs)
        if self.is_constructor:
            # An empty 'this' object must be created before
            # this constructor executes, or else this function
            # may assign values to matching names in a previous 'this' object.
            # Instead, all variables should be assigned to the latest
            # scope (last element of env.frames),
            # which will then be returned as a new object.
            env.new_this({})
            if self.hooks is not None:
                for method in self.hooks.values():
                    method.defined_as_method = True
        if self.defined_as_method:
            env.is_method_stack.append(True)
        else:
            env.is_method_stack.append(False)
        # Put function arguments into environment frame:
        arguments.assign_arguments(self.args, arg_values, env)
        result = execution.execute_lines(
            self.line_mgr,
            env,
            executing_constructor=self.is_constructor,
            supplied_hooks=self.hooks
        )
        # Remove the stack frame created by this function:
        env.pop()
        # Remove the last 'this' pointer.
        # This will remove the 'this' object used by a method,
        # or it will remove the empty 'this' object used by a
        # constructor.
        # TODO : defining a class inside another class may cause
        # issues, because the inner class may be considered both
        # a method and a constructor.
        if self.called_as_method or self.is_constructor:
            env.pop_this()
        # Reset called_as_method, since it is possible the next time
        # we are called, we won't be called as a method.
        # (this can happen with implicit 'this'. Another method can
        #  invoke a method on the same object with 'method()' instead of
        #  'this.method()')
        self.called_as_method = False
        env.is_method_stack.pop()
        if self.return_type is None or env.value_is_a(result, self.return_type):
            return result
        else:
            throw_exception('IncorrectReturnType', '{0} is not of type {1}'.format(result, self.return_type))
    
    def supply(self, env):
        """
        Gives a higher-order function a special environment.
        This provides a copy of the current function, updated
        with the correct environment.
        """
        # TODO : one possible alternative to using env.has_hook(function_object)
        # would be to allow each function to be supplied an environment only once.
        # A boolean variable could keep track of which functions already possess
        # the correct supplied environment.
        new_func = Function(self.name, self.args, [], env.copy())
        new_func.line_mgr = self.line_mgr
        new_func.defined_funcs = self.defined_funcs
        return new_func
        
    def __repr__(self):
        return '<function {0}({1}) -> {2}>'.format(
            self.name,
            str(self.args)[1:-1],
            self.line_mgr.format_lines()
        )

    def __str__(self):
        return repr(self)
