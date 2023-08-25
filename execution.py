import re

from tokens import tokenize_statement, \
                   seek_parenthesis_in_tokens
from ratio import Ratio
from exception import throw_exception, throw_exception_with_line
from table import Table
from control_flow import find_next_end_else
from trigger import Trigger
from imports import perform_import

import ast2
import function
import type_restrict
import type_tree
import builtin_method
import prepare_program
import env as environment
import operator_overload
import console
import strtools
import time_literal

def execute_lines(line_mgr, env, executing_constructor=False, supplied_hooks=None):
    """
    Executes lines of code in a given environment.
    """
    prgm_counter = 0
    cond_flag = False
    env.line_mgr = line_mgr
    line_mgr.classify_statements()
    while prgm_counter < len(line_mgr):
        env.prgm_counter = prgm_counter
        line = line_mgr[prgm_counter]
        directive = execute_statement(line_mgr.get_line_data(prgm_counter), executing_constructor, env)
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
                _, j = find_next_end_else(line_mgr, prgm_counter + 1, False)
                prgm_counter = j + 1
            elif directive[0] == ':hook':
                env.activate_hook(directive[1], supplied_hooks)
                prgm_counter += 1
            elif directive[0] == 'return':
                if directive[1] == 'this':
                    # Create a user-defined object.
                    # Do not use env.pop() because the function
                    # will automatically remove the stack frame
                    # upon completion.
                    obj = env.last()
                    # Allow the object to refer to itself
                    # TODO : assign the 'this' variable at the start
                    # of scope creation, not when it is returned.
                    obj['this'] = obj
                    for key, method in obj.items():
                        if key == '$eq' and method.__class__ is function.Function and env.has_hook(method):
                            # Methods must remember the environment of the object
                            # where they were defined.
                            obj[key] = method.supply(env)
                    return obj
                else:
                    value = eval_parentheses(directive[1], env)
                    # Functions that were defined in the current scope
                    # using a 'sub' statement or 'func' statement
                    # must be supplied with the current environment,
                    # so that closures work correctly.
                    # This does not apply to functions that were passed
                    # in as an argument, or functions produced by other means.
                    # In other words, existing function objects should not
                    # be re-supplied with the current environment, only newly
                    # created ones.
                    if function.is_function(value) and env.has_hook(value):
                        # TODO : instead of supplying an environment when a defined
                        # function is returned, supply it when the function is first
                        # defined. This will allow for more complex return values,
                        # such as a list of functions, to operate correctly as closures.
                        value = value.supply(env)
                    return value
            elif directive[0] == 'try':
                env.exception_push(prgm_counter)
                prgm_counter += 1
            elif directive[0] == 'throw':
                mirage = 'mirage'
                if len(directive) == 2 and (directive[1].startswith(mirage + ' ') or \
                   directive[1].startswith(mirage + '\t')):
                    constructor_call = directive[1][len(mirage) + 1:].lstrip()
                    directive[1] = constructor_call
                    i = constructor_call.find('(')
                    if i == -1:
                        throw_exception_with_line(
                            'InvalidSyntax',
                            'mirage keyword must be followed by a constructor call',
                            line_mgr,
                            prgm_counter
                        )
                    class_name = constructor_call[:i]
                    new_class = None
                    class_body = ['$type="{0}"'.format(class_name), 'return this']
                    if i + 1 < len(constructor_call) and constructor_call[i + 1] == ')':
                        # No arguments
                        new_class = function.Function(class_name, [], class_body)
                    else:
                        # 1 argument
                        new_class = function.Function(class_name, ['message'], class_body)
                    env.frames[0][class_name] = new_class
                    # TODO : this class should inherit from Exception, not Object.
                    env.new_type(['Object'], class_name)
                last_prgm_counter = prgm_counter
                prgm_counter = env.exception_pop()
                if prgm_counter is None:
                    throw_exception_with_line(
                        'UncaughtException',
                        'Thrown value ' + str(directive[1:]),
                        line_mgr,
                        last_prgm_counter
                    )
                else:
                    original_counter = prgm_counter
                    # Look for a matching catch statement
                    prgm_counter = find_catch(directive, line_mgr, prgm_counter, env)
                    if prgm_counter is None:
                        # We can't find a catch statement.
                        # Let the exception bubble up from its current scope.
                        env.exception_push(original_counter)
                        return Trigger(directive[1])
            elif directive[0] in ['catch', 'else']:
                kind, j = find_next_end_else(line_mgr, prgm_counter + 1, True)
                # Travel to the next end
                prgm_counter = j + 1
            elif directive[0] == 'end':
                # This is an isolated end statement. Ignore it.
                prgm_counter += 1
            else:
                prgm_counter += 1
        else:
            prgm_counter += 1
    # All functions should return something,
    # which is null for 'void' functions.
    return None

def find_catch(directive_list, line_mgr, prgm_counter, env):
    """
    Finds a matching catch statement for an object that was thrown.
    Returns the program counter for the catch statement, plus 1.
    """
    # TODO : allow for nested try-catch statements
    thrown = eval_parentheses(directive_list[1], env)
    while prgm_counter < len(line_mgr):
        line = line_mgr[prgm_counter]
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

directives = [':cond', ':j', ':jt', ':jf', 'return', 'try', 'throw',
              'catch', 'end', 'else', ':skiptoelse', ':hook',
              ':inc', ':dec']

def execute_statement(line_data, executing_constructor, env):
    """Executes a statement in a given environment."""
    stmt = line_data.line
    # Lines already have leading/trailing whitespace removed.
    # If the line has no content, do not execute it.
    if len(stmt) == 0:
        return
    if line_data.is_statement:
        tokens = tokenize_statement(stmt)
        if tokens[0] == 'print':
            if tokens[1] == 'this':
                print(env)
            else:
                console.display(eval_parentheses(tokens[1], env))
        elif tokens[0] == 'show':
            console.display(eval_parentheses(tokens[1], env), False)
        elif tokens[0] == 'super':
            env.extract(eval_parentheses(tokens[1], env))
        elif tokens[0] == 'import':
            perform_import(tokens[1], env)
        elif tokens[0] == 'func':
            function.define_single_line_function(tokens[1], executing_constructor, env)
        elif tokens[0] in directives:
            return tokens
        elif tokens[1] == '=':
            env.assign(tokens[0], eval_parentheses(tokens[2], env))
            last_assigned = env.get_last_assigned()
            if last_assigned.__class__ is Trigger:
                return ['throw', last_assigned.get_thrown()]
        elif tokens[1] == '+=':
            val = env.get(tokens[0])
            env.update(tokens[0], val + eval_parentheses(tokens[2], env))
    else:
        result = eval_parentheses(stmt, env)
        # An exception was thrown
        if result.__class__ is Trigger:
            return ['throw', result.get_thrown()]
    # No directive to be processed:
    return None

def apply_unary_ops_for_list(elems):
    i = len(elems) - 2
    while i >= 0:
        elem = elems[i]
        if elem in ast2.unary_ops:
            if elem == '~':
                elems[i : i+2] = [-elems[i + 1]]
            else:
                elems[i : i+2] = [not elems[i + 1]]
        i -= 1
    return elems

def apply_unary_ops_to_tokens(tokens):
    results = []
    for token in tokens:
        if type(token) is list:
            results.append(apply_unary_ops_for_list(token))
        else:
            results.append(token)
    return results

def evaluate_list(tokens, env):
    """
    Transforms a list of tokens containing square brackets
    into a proper list.
    
    e.g. ['[', '1', ',', '2', ']'] -> [[1, 2]]
    """
    results = []
    i = 0
    # TODO : should brackets include '{', '}'?
    brackets = ['[', ']']
    while i < len(tokens):
        token = tokens[i]
        if token == '[':
            j = strtools.find_matching(tokens[i + 1:], '[', ']')
            lst = []
            for elem in tokens[i+1 : i+j]:
                if elem != ',':
                    # Need to use the .keys() method of 'precedences'
                    # or else unhashable elements (such as lists) will throw an exception
                    if elem in brackets or elem in ast2.precedences.keys() or type(elem) is not str:
                        lst.append(elem)
                    else:
                        lst.append(eval_parentheses(elem, env))
            while '[' in lst:
                lst = evaluate_list(lst, env)
            results.append(lst)
            i += j
        elif token == '{':
            # TODO : allow nested lists and tables inside table literals
            j = strtools.find_matching(tokens[i + 1:], '{', '}')
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
    return apply_unary_ops_to_tokens(results)
    
def get_name(name, env):
    if type(name) is str and env.has_name(name):
        return env.get(name)
    return name

def is_index_valid(current):
    return type(current) is list and len(current) == 1

def index_lists(tokens, env):
    i = 1
    while i < len(tokens):
        if i >= 2 and tokens[i - 2] == '.':
            i += 1
            continue
        prev = convert_value(get_name(tokens[i - 1], env), env)
        current = get_name(tokens[i], env)
        # For an expression such as x[i], x is 'prev' and [i] is 'current',
        # so [i] should always be a generic list, not a restricted one.
        if is_index_valid(current):
            if type_restrict.is_considered_list(prev):
                index = get_name(current[0], env)
                if type(index) in [int, long]:
                    tokens[i-1 : i+1] = [prev[index]]
                else:
                    env.throw_exception(
                        'NonIntegerIndex',
                        'Trying to index the list {0} with a non-integer index {1}'.format(
                            prev, index
                        )
                    )
            elif is_string(prev):
                index = get_name(current[0], env)
                tokens[i-1 : i+1] = [strtools.index_string(prev, index)]
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
        return parsed_tokens
    else:
        return env.get_tokens(expr)

def evaluate_expression(expr, env, parsed_tokens=None):
    """
    Evaluates an expression by converting it to an AST
    and evaluating individual operators at certain indices.
    """
    tokens = retrieve_tokens(expr, env, parsed_tokens)
    indices = env.get_indices(tokens)
    return evaluate_operators(tokens, indices, env)

def is_unary(tokens, idx):
    """
    Returns True if tokens[idx] has an operator that should be considered unary,
    else False.
    """
    return idx == 0 or tokens[idx - 1] in ast2.precedences or tokens[idx - 1] == ','

def transform_string_literals(tokens):
    for i in xrange(len(tokens)):
        token = tokens[i]
        if type(token) is str and len(token) >= 2 and token[0] == '"' and token[-1] == '"':
            tokens[i] = strtools.CapString(token[1:-1])

def xor(left, right):
    return (left and not right) or ((not left) and right)

def evaluate_operators(tokens, indices, env):
    """
    Evaluates an expression based on a list of tokens,
    indices where the operators are located, and
    environment env.
    """
    brackets = ['[', ']', '{', '}']
    transform_string_literals(tokens)
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
        left, right = promote_values(left, right, op)
        # TODO : support user-defined methods such as $eq, $notEq when evaluating operators
        if is_dot:
            tokens[idx-1 : idx+2] = [environment.get_typed_value(left[right])]
        elif op != ' of ' and operator_overload.ready_for_overload(op, left, right):
            # Perform operator overloading
            result = operator_overload.operator_overload(op, left, right, idx, tokens, env)
            return_val = result['return_val']
            if result['is_unary']:
                tokens[idx : idx+2] = [return_val]
            else:
                tokens[idx-1 : idx+2] = [return_val]
        elif op == '+':
            tokens[idx-1 : idx+2] = [left + right]
        elif op == '-':
            tokens[idx-1 : idx+2] = [left - right]
        elif op == '~':
            tokens[idx : idx+2] = [-right]
        elif op == '*':
            tokens[idx-1 : idx+2] = [left * right]
        elif op == '/':
            tokens[idx-1 : idx+2] = [divide(left, right)]
        elif op == '%':
            tokens[idx-1 : idx+2] = [left % right]
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
        elif op == 'not ':
            tokens[idx : idx+2] = [not right]
        elif op == '^':
            tokens[idx-1 : idx+2] = [left ** right]
        elif op == ':':
            tokens[idx-1 : idx+2] = [Ratio(left, right)]
        elif op == ' of ':
            tokens[idx-1 : idx+2] = [type_restrict.type_restrict(left, right, env)]
        elif op == ' xor ':
            tokens[idx-1 : idx+2] = [xor(left, right)]
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
    tokens = retrieve_tokens(expr, env, parsed_tokens)
    tokens = call_functions(tokens, env)
    if tokens.__class__ is Trigger:
        return tokens
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
            offset = strtools.find_matching(args[i + 1:])
            if offset == -1:
                throw_exception('UnmatchedOpeningParenthesis', args)
            buffer += args[i : i+offset]
            i += offset
        elif char == '[':
            offset = strtools.find_matching(args[i + 1:], '[', ']')
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
    while i < len(tokens):
        token = tokens[i]
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
                i -= 1
            else:
                tokens[i] = return_val
                i += 1
        else:
            i += 1
        prev_token = token
    return tokens

def is_string(val):
    """
    Returns True if val is a string, else False.
    """
    return val.__class__ is strtools.CapString

def divide(a, b):
    if type(a) is float or type(b) is float or \
       (type(a) in [int, long] and type(b) in [int, long]):
        return float(a) / float(b)
    # Default behavior for Ratio objects, and any other numeric
    # types (such as complex)
    return a / b
            
def promote_values(left, right, op):
    """
    Converts values left and right to proper types
    so that operators can act on them.
    For instance, Ratio + Integer should be a Ratio.
    """
    # Detect the operators >, >=, <, <=
    is_left_str = is_string(left)
    is_right_str = is_string(right)
    # TODO : it may be possible to remove the initial isinstance()
    #        call by fixing the xrange issue:
    #        evaluate_operators(tokens, xrange(len(tokens) - 1), env)
    if isinstance(op, str) and ('>' in op or '<' in op) and xor(is_left_str, is_right_str):
        return left, right
    def stringify(val):
        if not is_string(val):
            return strtools.CapString(str(val), False)
        return val
    if left is None:
        return left, right
    elif is_left_str:
        return left, stringify(right)
    elif is_right_str:
        return stringify(left), right
    elif type(left) is float:
        return left, float(right)
    elif type(right) is float:
        return float(left), right
    elif left.__class__ is Ratio and type(right) in [int, long]:
        return left, Ratio(right, 1)
    elif type(left) in [int, long] and right.__class__ is Ratio:
        return Ratio(left, 1), right
    else:
        return left, right

def construct_valid_var_first_char_set():
    # Variables can start with a dollar sign, underscore,
    # or any uppercase or lowercase letter.
    results = '$_'
    for letter_ord in xrange(ord('A'), ord('Z') + 1):
        results += chr(letter_ord)
    for letter_ord in xrange(ord('a'), ord('z') + 1):
        results += chr(letter_ord)
    return set(results)

brackets = ['[', ']']
valid_var_first_chars = construct_valid_var_first_char_set()
valid_digits = set('0123456789')

def convert_value(val, env):
    """
    Given a value in string form, converts to an int, float, etc.
    Or, given a variable name, retrieves the value of that variable.
    """
    if (type(val) is not str) or val in brackets:
        return val
    if len(val) == 0:
        return None
    first_char = val[0]
    # All numeric literals start with a digit.
    # Formats such as ".25" are not allowed: should be written as "0.25"
    if first_char in valid_digits:
        try:
            return int(val)
        except ValueError:
            try:
                return float(val)
            except ValueError:
                pass
    elif first_char in valid_var_first_chars:
        # Grab a variable's value:
        return env.get(val)
    elif first_char == '#':
        # This is a tag
        return val
    elif first_char == '\\':
        # This is a time literal
        return time_literal.make_duration(val[1:], env)
    elif len(val) >= 2:
        if (val[0] == '"' and val[-1] == '"') or \
           (val[0] == "'" and val[-1] == "'"):
            return strtools.CapString(val[1:-1])
        elif val[0] == '[' and val[-1] == ']':
            result = parse_list(val[1:-1], env)
            return result
    if val in ast2.precedences or val == ',':
        # This is an operator
        return None
    env.throw_exception(
        'UnrecognizedValue',
        '{0} cannot be interpreted as an Int, Double, Tag, String, List, operator, or variable name'.format(val)
    )

def parse_list(list_contents, env):
    """
    Given list contents (the internals of the list without square brackets)
    returns the list with all elements evaluated in the current environment.
    """
    elems = split_args(list_contents)
    evaluated = [eval_parentheses(elem, env) for elem in elems]
    return evaluated
    