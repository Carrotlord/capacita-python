import re

from tokens import tokenize_statement
from ast2 import AST
from ribbon import Ribbon
from ratio import Ratio
from console import display
from exception import throw_exception
from strtools import find_matching
from builtin_function import BuiltinFunction
from table import Table
from control_flow import find_next_end_else
from trigger import Trigger
from imports import perform_import

def dot_operator(obj, name, env):
    if type(obj) is str and re.match(r'\$?[A-Za-z_][A-Za-z_0-9]*', obj):
        obj = env.get(obj)
    obj = convert_value(obj, env)
    if type(obj) is list:
        if name == 'length' or name == 'size':
            length = len(obj)
            return BuiltinFunction('constant', [], lambda: length)
        elif name == 'pop':
            last_elem = obj.pop()
            return BuiltinFunction('constant', [], lambda: last_elem)
        elif name == 'push':
            def func_push(new_elem):
                obj.append(new_elem)
                return obj
            return BuiltinFunction('list', ['new_elem'], func_push)
    elif type(obj) is dict:
        # This is a method call
        env.new_this(obj)
        method = obj[name]
        method.activate_method()
        return method
    elif type(obj) in [int, float]:
        if name == 'next':
            return BuiltinFunction('constant', [], lambda: obj + 1)
        elif name == 'previous':
            return BuiltinFunction('constant', [], lambda: obj - 1)
    elif obj.__class__ is Table:
        if name == 'length' or name == 'size':
            return BuiltinFunction('constant', [], lambda: len(obj))
        elif name == 'keys':
            return BuiltinFunction('constant', [], lambda: obj.keys())
        elif name == 'hasKey':
            return BuiltinFunction('hasKey', ['key'], lambda key: obj.has_key(key))
    throw_exception('NoSuchAttribute', str(obj) + ' object has no attribute ' + name)

def execute_lines(lines, env):
    """
    Executes lines of code in a given environment.
    """
    prgm_counter = 0
    cond_flag = False
    while prgm_counter < len(lines):
        line = lines[prgm_counter]
        directive = execute_statement(line, env)
        if directive is not None:
            if directive[0] == ':cond':
                cond_flag = eval_parentheses(directive[1], env)
                prgm_counter += 1
            elif directive[0] == ':j':
                prgm_counter = int(directive[1])
            elif (cond_flag and directive[0] == ':jt') or \
                 ((not cond_flag) and directive[0] == ':jf'):
                prgm_counter = int(directive[1])
            elif directive[0] == ':skiptoelse':
                # Nothing was thrown in this try clause
                _, j = find_next_end_else(lines, prgm_counter + 1, False)
                prgm_counter = j + 1
            elif directive[0] == 'return':
                if directive[1] == 'this':
                    # Create a user-defined object.
                    # Do not use env.pop() because the function
                    # will automatically remove the stack frame
                    # upon completion.
                    obj = env.last()
                    # Allow the object to refer to itself
                    obj['this'] = obj
                    return obj
                else:
                    value = eval_parentheses(directive[1], env)
                    if str(value).startswith('<function'):
                        value = value.supply(env)
                    return value
            elif directive[0] == 'try':
                env.exception_push(prgm_counter)
                prgm_counter += 1
            elif directive[0] == 'throw':
                prgm_counter = env.exception_pop()
                if prgm_counter is None:
                    throw_exception('UncaughtException', 'Thrown value ' + str(directive[1:]))
                else:
                    original_counter = prgm_counter
                    # Look for a matching catch statement
                    prgm_counter = find_catch(directive, lines, prgm_counter, env)
                    if prgm_counter is None:
                        # We can't find a catch statement.
                        # Let the exception bubble up from its current scope.
                        env.exception_push(original_counter)
                        return Trigger(directive[1])
            elif directive[0] in ['catch', 'else']:
                kind, j = find_next_end_else(lines, prgm_counter + 1, True)
                # Travel to the next end
                prgm_counter = j + 1
            elif directive[0] == 'end':
                # This is an isolated end statement. Ignore it.
                prgm_counter += 1
            else:
                prgm_counter += 1
        else:
            prgm_counter += 1

def find_catch(directive_list, lines, prgm_counter, env):
    """
    Finds a matching catch statement for an object that was thrown.
    Returns the program counter for the catch statement, plus 1.
    """
    # TODO : allow for nested try-catch statements
    thrown = eval_parentheses(directive_list[1], env)
    while prgm_counter < len(lines):
        line = lines[prgm_counter]
        if line.startswith('catch '):
            caught = line[6:].split(' ')
            if len(caught) == 1:
                # This will catch any object thrown:
                var = caught[0]
                env.assign(var, thrown)
                return prgm_counter + 1
            else:
                kind, var = caught
                if env.value_is_a(thrown, kind):
                    env.assign(var, thrown)
                    return prgm_counter + 1
        elif line == 'else' or line == 'end':
            # Nothing was thrown, so execute else clause
            env.exception_pop()
            return prgm_counter + 1
        prgm_counter += 1
    # Cannot finish try catch:
    return None
            
def is_statement(query):
    """Returns True if query is a statement, else False."""
    if query.startswith('print ') or query.startswith('show ') or \
       query.startswith('return ') or query.startswith(':') or \
       query == 'try' or query == 'end' or query == 'else' or \
       query.startswith('throw ') or query.startswith('catch ') or \
       query.startswith('super ') or query.startswith('import '):
        return True
    comparators = ['==', '!=', '>=', '<=']
    ast = AST(query)
    tokens = ast.parse()
    for token in tokens:
        if '=' in token and token not in comparators:
            return True
    return False

def execute_statement(stmt, env):
    """Executes a statement in a given environment."""
    directives = [':cond', ':j', ':jt', ':jf', 'return', 'try', 'throw',
                  'catch', 'end', 'else', ':skiptoelse']
    stmt = stmt.strip()
    if len(stmt) == 0:
        return
    if is_statement(stmt):
        tokens = tokenize_statement(stmt)
        if tokens[0] == 'print':
            if tokens[1] == 'this':
                print(env)
            else:
                display(eval_parentheses(tokens[1], env))
        elif tokens[0] == 'show':
            display(eval_parentheses(tokens[1], env), False)
        elif tokens[0] == 'super':
            env.merge(eval_parentheses(tokens[1], env))
        elif tokens[0] == 'import':
            perform_import(tokens[1], env)
        elif tokens[0] in directives:
            return tokens
        elif tokens[1] == '=':
            env.assign(tokens[0], eval_parentheses(tokens[2], env))
            last_assigned = env.get_last_assigned()
            if last_assigned.__class__ is Trigger:
                return ['throw', last_assigned.get_thrown()]
        elif tokens[1] == '+=':
            val = env.get(tokens[0])
            env.update(tokens[0], plus(val, eval_parentheses(tokens[2], env)))
    else:
        result = eval_parentheses(stmt, env)
        # An exception was thrown
        if result.__class__ is Trigger:
            return ['throw', result.get_thrown()]
    # No directive to be processed:
    return None

def evaluate_list(tokens, env):
    """
    Transforms a list of tokens containing square brackets
    into a proper list.
    
    e.g. ['[', '1', ',', '2', ']'] -> [[1, 2]]
    """
    results = []
    i = 0
    brackets = ['[', ']']
    while i < len(tokens):
        token = tokens[i]
        if token == '[':
            j = find_matching(tokens[i + 1:], '[', ']')
            lst = []
            for elem in tokens[i+1 : i+j]:
                if elem != ',':
                    if elem in brackets or (type(elem) is not str):
                        lst.append(elem)
                    else:
                        lst.append(eval_parentheses(elem, env))
            while '[' in lst:
                lst = evaluate_list(lst, env)
            results.append(lst)
            i += j
        elif token == '{':
            # TODO : allow nested lists and tables inside table literals
            j = find_matching(tokens[i + 1:], '{', '}')
            table = Table()
            is_key = True
            last_key = None
            last_val = None
            for elem in tokens[i+1 : i+j]:
                if elem not in [',', '|']:
                    if is_key:
                        last_key = eval_parentheses(elem, env)
                        is_key = False
                    else:
                        last_val = eval_parentheses(elem, env)
                        is_key = True
                        table.put(last_key, last_val)
            results.append(table)
            i += j
        else:
            results.append(token)
        i += 1
    return results
    
def get_name(name, env):
    if type(name) is str and env.has_name(name):
        return env.get(name)
    return name

def index_lists(tokens, env):
    i = 1
    while i < len(tokens):
        prev = get_name(tokens[i - 1], env)
        current = get_name(tokens[i], env)
        if type(prev) is list and type(current) is list and \
           len(current) == 1:
            index = get_name(current[0], env)
            if type(index) is int:
                tokens[i-1 : i+1] = [prev[index]]
        elif prev.__class__ is Table and type(current) is list and \
             len(current) == 1:
             key = get_name(current[0], env)
             tokens[i-1 : i+1] = [prev.get(key)]
        else:
            i += 1
    return tokens

def evaluate_expression(expr, env):
    """
    Evaluates an expression by converting it to an AST
    and evaluating individual operators at certain indices.
    """
    ast = AST(expr)
    tokens = ast.parse()
    indices = ast.collapse_indices(ast.build_indices())
    return evaluate_operators(tokens, indices, env)
    
def evaluate_operators(tokens, indices, env):
    """
    Evaluates an expression based on a list of tokens,
    indices where the operators are located, and
    environment env.
    """
    brackets = ['[', ']', '{', '}']
    for idx in indices:
        # TODO : checking bounds should no longer be
        # necessary after fixing the xrange issue.
        # (passing in an xrange as operator indices)
        if idx >= len(tokens):
            break
        op = tokens[idx]
        is_dot = op == '.'
        if idx > 0:
            left = convert_value(tokens[idx-1], env)
        else:
            left = None
        if idx + 1 >= len(tokens):
            # This index is not valid:
            break
        if not is_dot:
            right = convert_value(tokens[idx+1], env)
        else:
            right = tokens[idx+1]
        if left in brackets or right in brackets:
            break
        left, right = promote_values(left, right)
        if op == '+':
            tokens[idx-1 : idx+2] = [plus(left, right)]
        elif op == '-':
            if idx == 0:
                tokens[idx : idx+2] = [-right]
            else:
                tokens[idx-1 : idx+2] = [left - right]
        elif op == '*':
            tokens[idx-1 : idx+2] = [left * right]
        elif op == '/':
            # Todo allow for better ratio and int division
            tokens[idx-1 : idx+2] = [float(left) / float(right)]
        elif op == '^':
            tokens[idx-1 : idx+2] = [left ** right]
        elif op == ':':
            tokens[idx-1 : idx+2] = [Ratio(left, right)]
        elif op == '==':
            tokens[idx-1 : idx+2] = [left == right]
        elif op == '!=':
            tokens[idx-1 : idx+2] = [left != right]
        elif op == '>=':
            tokens[idx-1 : idx+2] = [left >= right]
        elif op == '<=':
            tokens[idx-1 : idx+2] = [left <= right]
        elif op == '>':
            tokens[idx-1 : idx+2] = [left > right]
        elif op == '<':
            tokens[idx-1 : idx+2] = [left < right]
        elif op == ' and ':
            tokens[idx-1 : idx+2] = [left and right]
        elif op == ' or ':
            tokens[idx-1 : idx+2] = [left or right]
        elif op == ' xor ':
            tokens[idx-1 : idx+2] = [(left and not right) or ((not left) and right)]
        elif op == 'not ':
            tokens[idx : idx+2] = [not right]
        elif op == '.':
            tokens[idx-1 : idx+2] = [left[right]]
    stage = 0
    while len(tokens) != 1:
        if stage == 0:
            tokens = evaluate_list(tokens, env)
            stage = 1
        elif stage == 1:
            tokens = index_lists(tokens, env)
            stage = 2
        elif stage == 2:
            input_tokens = tokens
            # TODO : avoid having to pass in an xrange of possible operator indices
            tokens = evaluate_operators(tokens, xrange(len(tokens) - 1), env)
            # If the value returned is no longer the outer list, it means
            # an inner list is the result:
            if tokens is not input_tokens:
                return tokens
            stage = 3
        elif stage == 3:
            throw_exception('ExprEval', str(tokens) + ' cannot be converted into a single value')
    # Return the resulting (single) value without the outer list.
    return convert_value(tokens[0], env)

def eval_parentheses(expr, env):
    """
    Recursively evaluates expressions enclosed in parentheses,
    which change the order-of-operations for the expression.
    """
    ast = AST(expr)
    tokens = ast.parse()
    tokens = call_functions(tokens, env)
    if tokens.__class__ is Trigger:
        return tokens
    # For function values, do not transform the value to a string:
    if len(tokens) == 1 and (str(tokens[0]).startswith('<function') or \
        type(tokens[0]) is list or type(tokens[0]) is dict):
        return tokens[0]
    expr = ''.join(str(token) for token in tokens)
    paren_open = expr.find('(')
    if paren_open == -1:
        return evaluate_expression(expr, env)
    else:
        paren_close = find_matching(expr[paren_open + 1:]) + paren_open
        if paren_close == -1:
            throw_exception('UnmatchedOpeningParenthesis', expr)
        left = expr[0:paren_open]
        center = expr[paren_open + 1:paren_close]
        right = expr[paren_close + 1:]
        return eval_parentheses(left + str(eval_parentheses(center, env)) + right, env)
        
def split_args(args):
    """
    Given a comma-separated argument list, returns the individual
    arguments as a list.
    e.g. '(x+1)*8, y, 25' -> ['(x+1)*8', ' y', ' 25']
    """
    i = 0
    buffer = ''
    results = []
    while i < len(args):
        char = args[i]
        if char == '(':
            offset = find_matching(args[i + 1:])
            if offset == -1:
                throw_exception('UnmatchedOpeningParenthesis', args)
            buffer += args[i : i+offset]
            i += offset
        elif char == '[':
            offset = find_matching(args[i + 1:], '[', ']')
            if offset == -1:
                throw_exception('UnmatchedOpeningSquareBracket', args)
            buffer += args[i : i+offset]
            i += offset
        elif char == ',':
            results.append(buffer)
            buffer = ''
            i += 1
        else:
            buffer += char
            i += 1
    if len(buffer) > 0:
        results.append(buffer)
    return results

def call_functions(tokens, env):
    """
    Replaces function calls with the return value of each function.
    """
    i = 0
    prev_token = None
    for token in tokens:
        match_obj = re.match('([A-Za-z_][A-Za-z_0-9]*)\((.*)\)', token)
        if match_obj:
            func_name = match_obj.group(1)
            func_args = match_obj.group(2)
            arg_list = split_args(func_args)
            # Evaluate all argument expressions:
            arg_values = [eval_parentheses(arg, env) for arg in arg_list]
            if prev_token == '.':
                obj_name = tokens[i - 2]
                func_obj = dot_operator(obj_name, func_name, env)
            else:
                func_obj = env.get(func_name)
            return_val = func_obj.execute(arg_values, env)
            # Was an exception thrown during this function?
            if return_val.__class__ is Trigger:
                return return_val
            # Handle function values separately from normal values
            str_val = str(return_val)
            if (len(str_val) > 0 and str_val.startswith('<function')) or \
                type(return_val) is list or type(return_val) is dict:
                if prev_token == '.':
                    tokens[i-2 : i+1] = [return_val]
                else:
                    tokens[i] = return_val
            else:
                if prev_token == '.':
                    tokens[i-2 : i+1] = [str_val]
                else:
                    tokens[i] = str_val
        i += 1
        prev_token = token
    return tokens

def is_string(val):
    """
    Returns True if val is a string surrounded in quotes,
    else False.
    """
    if type(val) is not str:
        return False
    else:
        return len(val) >= 2 and val[0] == '"' and val[-1] == '"'

def plus(a, b):
    """Concatenates strings or returns sum of a and b."""
    a_str = is_string(a)
    b_str = is_string(b)
    if a_str and b_str:
        return '"{0}{1}"'.format(a[1:-1], b[1:-1])
    elif a_str:
        return '"{0}{1}"'.format(a[1:-1], b)
    elif b_str:
        return '"{0}{1}"'.format(a, b[1:-1])
    else:
        return a + b
            
def promote_values(left, right):
    """
    Converts values left and right to proper types
    so that operators can act on them.
    For instance, Ratio + Integer should be a Ratio.
    """
    def stringify(val):
        if not is_string(val):
            return '"{0}"'.format(val)
        else:
            return val
    if left is None:
        return left, right
    elif is_string(left):
        return left, stringify(right)
    elif is_string(right):
        return stringify(left), right
    elif type(left) is float:
        return left, float(right)
    elif type(right) is float:
        return float(left), right
    elif left.__class__ is Ratio and type(right) is int:
        return left, Ratio(right, 1)
    elif type(left) is int and right.__class__ is Ratio:
        return Ratio(left, 1), right
    else:
        return left, right

def convert_value(val, env):
    """
    Given a value in string form, converts to an int, float, etc.
    Or, given a variable name, retrieves the value of that variable.
    """
    brackets = ['[', ']']
    if (type(val) is not str) or val in brackets:
        return val
    if val == 'True':
        return True
    if val == 'False':
        return False
    if val == 'None':
        return None
    if re.match(r'\$?[A-Za-z_][A-Za-z_0-9]*', val):
        # Grab a variable's value:
        return env.get(val)
    if re.match(r'#\$?[A-Za-z_][A-Za-z_0-9]*', val):
        # This is a tag
        return val
    if len(val) >= 2:
        if val[0] == "'" and val[-1] == "'":
            return '"{0}"'.format(val[1:-1])
        elif val[0] == '"' and val[-1] == '"':
            return val
        elif val[0] == '`' and val[-1] == '`':
            return Ribbon(val[1:-1])
        elif val[0] == '[' and val[-1] == ']':
            result = parse_list(val[1:-1], env)
            return result
    try:
        return int(val)
    except ValueError:
        try:
            return float(val)
        except ValueError:
            return None

def parse_list(list_contents, env):
    """
    Given list contents (the internals of the list without square brackets)
    returns the list with all elements evaluated in the current environment.
    """
    elems = split_args(list_contents)
    evaluated = [eval_parentheses(elem, env) for elem in elems]
    return evaluated
    