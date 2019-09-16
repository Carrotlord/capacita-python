import re

from tokens import tokenize_statement, \
                   seek_parenthesis_in_tokens
from ast2 import AST, precedences
from ribbon import Ribbon
from ratio import Ratio
from console import display
from exception import throw_exception
from strtools import find_matching, escape, index_string
from table import Table
from control_flow import find_next_end_else
from trigger import Trigger
from imports import perform_import

import function
import type_restrict
import type_tree
import builtin_method
import prepare_program
import env as environment

def execute_lines(lines, env, executing_constructor=False):
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
            elif directive[0] == ':inc':
                var_name = directive[1]
                env.update_numeric(var_name, 1)
                prgm_counter += 1
            elif directive[0] == ':dec':
                var_name = directive[1]
                env.update_numeric(var_name, -1)
                prgm_counter += 1
            elif directive[0] == ':skiptoelse':
                # Nothing was thrown in this try clause
                _, j = find_next_end_else(lines, prgm_counter + 1, False)
                prgm_counter = j + 1
            elif directive[0] == ':hook':
                if executing_constructor:
                    this_obj = env.pop_this()
                env.activate_hook(directive[1])
                if executing_constructor:
                    env.new_this(this_obj)
                prgm_counter += 1
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

def is_assignment_statement(line):
    i = 0
    length = len(line)
    # The operators !=, >=, and <= start with !, >, or <
    starters = '!><'
    in_quotes = False
    while i < length:
        if prepare_program.is_quote(line, i):
            in_quotes = not in_quotes
        if not in_quotes:
            current_char = line[i]
            if current_char == '=':
                if i == 0 or i == length - 1:
                    throw_exception(
                        'SyntaxError',
                        'Statement begins or ends with an equals sign: ' + line
                    )
                elif line[i + 1] == '=':
                    # Double equals sign. Skip the next character.
                    i += 1
                elif line[i - 1] not in starters:
                    # This must be an assignment statement.
                    return True
        i += 1
    return False

def is_statement(query):
    """Returns True if query is a statement, else False."""
    if query.startswith('print ') or query.startswith('show ') or \
       query.startswith('return ') or query.startswith(':') or \
       query == 'try' or query == 'end' or query == 'else' or \
       query.startswith('throw ') or query.startswith('catch ') or \
       query.startswith('super ') or query.startswith('import ') or \
       query.startswith('func '):
        return True
    return is_assignment_statement(query)

def execute_statement(stmt, env):
    """Executes a statement in a given environment."""
    directives = [':cond', ':j', ':jt', ':jf', 'return', 'try', 'throw',
                  'catch', 'end', 'else', ':skiptoelse', ':hook',
                  ':inc', ':dec']
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
            env.extract(eval_parentheses(tokens[1], env))
        elif tokens[0] == 'import':
            perform_import(tokens[1], env)
        elif tokens[0] == 'func':
            function.define_single_line_function(tokens[1], env)
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

def is_index_valid(current):
    return type(current) is list and len(current) == 1

def index_lists(tokens, env):
    i = 1
    while i < len(tokens):
        prev = get_name(tokens[i - 1], env)
        current = get_name(tokens[i], env)
        # For an expression such as x[i], x is 'prev' and [i] is 'current',
        # so [i] should always be a generic list, not a restricted one.
        if is_index_valid(current):
            if type_restrict.is_considered_list(prev):
                index = get_name(current[0], env)
                if type(index) in [int, long]:
                    tokens[i-1 : i+1] = [prev[index]]
                else:
                    throw_exception(
                        'NonIntegerIndex',
                        'Trying to index the list {0} with a non-integer index {1}'.format(
                            prev, index
                        )
                    )
            elif is_string(prev):
                index = get_name(current[0], env)
                tokens[i-1 : i+1] = [index_string(prev, index)]
            elif prev.__class__ is Table:
                key = get_name(current[0], env)
                tokens[i-1 : i+1] = [prev.get(key)]
            else:
                i += 1
        else:
            i += 1
    return tokens

def retrieve_tokens(expr, env, parsed_tokens=None):
    """
    Retrieves (ast, tokens) from a string expression.
    tokens is the token list generated from the expression.
    ast is the abstract syntax tree associated with the expression.
    If parsed_tokens is provided, expr is ignored, and a generic
    AST will be returned instead.
    """
    if parsed_tokens is not None:
        return AST(), parsed_tokens
    else:
        ast = AST(expr)
        tokens = env.get_from_expr_cache(expr)
        if tokens is None:
            tokens = ast.parse()
            env.add_to_expr_cache(expr, tokens)
        return ast, tokens

def evaluate_expression(expr, env, parsed_tokens=None):
    """
    Evaluates an expression by converting it to an AST
    and evaluating individual operators at certain indices.
    """
    ast, tokens = retrieve_tokens(expr, env, parsed_tokens)
    indices = ast.collapse_indices(ast.build_indices(tokens))
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
            # TODO : here there is a check if tokens[idx - 1] is an operator
            # a more robust method may be to apply ast.merge_negatives(tokens)
            # to the token list before the code reaches this point
            if idx == 0 or tokens[idx - 1] in precedences:
                tokens[idx : idx+2] = [-right]
            else:
                tokens[idx-1 : idx+2] = [left - right]
        elif op == '*':
            tokens[idx-1 : idx+2] = [left * right]
        elif op == '/':
            # Todo allow for better ratio and int division
            tokens[idx-1 : idx+2] = [float(left) / float(right)]
        elif op == '%':
            tokens[idx-1 : idx+2] = [left % right]
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
        elif op == ' of ':
            tokens[idx-1 : idx+2] = [type_restrict.type_restrict(left, right, env)]
        elif op == '.':
            tokens[idx-1 : idx+2] = [environment.get_typed_value(left[right])]
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

def eval_parentheses(expr, env, parsed_tokens=None):
    """
    Recursively evaluates expressions enclosed in parentheses,
    which change the order-of-operations for the expression.
    """
    # List elements are sometimes already-evaluated expressions,
    # which may be floats, ints, etc. instead of string expressions.
    # In that case, just return the value instead of attempting
    # to evaluate the expression.
    if expr is not None and type(expr) is not str:
        return expr
    _, tokens = retrieve_tokens(expr, env, parsed_tokens)
    tokens = call_functions(tokens, env)
    if tokens.__class__ is Trigger:
        return tokens
    # For function values, do not transform the value to a string:
    # TODO : is the following if-statement still necessary?
    # (since intermediate values are no longer converted back to strings)
    if len(tokens) == 1 and (str(tokens[0]).startswith('<function') or \
        type(tokens[0]) is list or type(tokens[0]) is dict):
        return tokens[0]
    token_index_containing_paren = seek_parenthesis_in_tokens(tokens)
    if token_index_containing_paren is None:
        return evaluate_expression(None, env, tokens)
    else:
        left_tokens = tokens[0:token_index_containing_paren]
        right_tokens = tokens[token_index_containing_paren + 1:]
        # Remove parentheses surrounding the center token.
        paren_internals = tokens[token_index_containing_paren][1:-1]
        center_result = eval_parentheses(paren_internals, env)
        return eval_parentheses(None, env, left_tokens + [center_result] + right_tokens)

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
        if type(token) is not str:
            match_obj = None
        else:
            match_obj = re.match(r'(\$?[A-Za-z_][A-Za-z_0-9]*)\((.*)\)', token)
        if match_obj:
            func_name = match_obj.group(1)
            func_args = match_obj.group(2)
            arg_list = split_args(func_args)
            # Evaluate all argument expressions:
            arg_values = [eval_parentheses(arg, env) for arg in arg_list]
            if prev_token == '.':
                obj_name = tokens[i - 2]
                func_obj = builtin_method.dot_operator(obj_name, func_name, env)
            else:
                func_obj = env.get(func_name)
            return_val = func_obj.execute(arg_values, env)
            # Was an exception thrown during this function?
            if return_val.__class__ is Trigger:
                return return_val
            # Replace the function call with the return value of the function
            if prev_token == '.':
                # Replace a method call
                tokens[i-2 : i+1] = [return_val]
            else:
                tokens[i] = return_val
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
            return '"{0}"'.format(escape(val[1:-1]))
        elif val[0] == '"' and val[-1] == '"':
            return escape(val)
        elif val[0] == '`' and val[-1] == '`':
            return Ribbon(escape(val[1:-1]))
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
    