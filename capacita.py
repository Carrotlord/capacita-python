# Use Python 2, not Python 3
# @author Jiangcheng Oliver Chu

import re
import sys

from ratio import Ratio
from ast2 import AST
from control_flow import prepare_control_flow
from ribbon import Ribbon
from env import Environment
from console import display, literal
from tokens import tokenize_statement
from fileio import file_to_str
from exception import throw_exception

def execute_program(prgm):
    """Executes a program given as a string."""
    lines = prgm.split('\n')
    lines = [line.strip() for line in lines]
    lines = prepare_control_flow(lines)
    env = Environment()
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
            else:
                prgm_counter += 1
        else:
            prgm_counter += 1

def execute_statement(stmt, env):
    """Executes a statement in a given environment."""
    directives = [':cond', ':j', ':jt', ':jf']
    stmt = stmt.strip()
    if len(stmt) == 0:
        return
    tokens = tokenize_statement(stmt)
    if tokens[0] == 'print':
        display(eval_parentheses(tokens[1], env))
    elif tokens[0] == 'show':
        display(eval_parentheses(tokens[1], env), False)
    elif tokens[0] in directives:
        return tokens
    elif tokens[1] == '=':
        env.assign(tokens[0], eval_parentheses(tokens[2], env))
    elif tokens[1] == '+=':
        val = env.get(tokens[0])
        env.update(tokens[0], plus(val, eval_parentheses(tokens[2], env)))
    # No directive to be processed:
    return None
    
def convert_value(val, env):
    """
    Given a value in string form, converts to an int, float, etc.
    Or, given a variable name, retrieves the value of that variable.
    """
    if type(val) is not str:
        return val
    if val == 'True':
        return True
    if val == 'False':
        return False
    if val == 'None':
        return None
    if re.match('[A-Za-z_][A-Za-z_0-9]*', val):
        # Grab a variable's value:
        return env.get(val)
    if len(val) >= 2:
        if val[0] == "'" and val[-1] == "'":
            return '"{0}"'.format(val[1:-1])
        elif val[0] == '"' and val[-1] == '"':
            return val
        elif val[0] == '`' and val[-1] == '`':
            return Ribbon(val[1:-1])
    try:
        return int(val)
    except ValueError:
        try:
            return float(val)
        except ValueError:
            return None

def is_statement(query):
    """Returns True if query is a statement, else False."""
    if query.startswith('print ') or query.startswith('show '):
        return True
    comparators = ['==', '!=', '>=', '<=']
    ast = AST(query)
    tokens = ast.parse()
    for token in tokens:
        if '=' in token and token not in comparators:
            return True
    return False
    
def store_program():
    """
    Stores a program line-by-line until :end statement is reached.
    """
    lines = ""
    next_line = None
    while True:
        next_line = raw_input()
        if next_line == ':end':
            break
        lines += next_line + '\n'
    return lines

def repl():
    """
    Read-eval-print loop. Whole programs can be run by using
    the ':program' directive, ending with ':end'.
    Use the 'this' keyword to see the current environment frames.
    """
    env = Environment()
    while True:
        expr = raw_input('Capacita> ')
        expr = expr.strip()
        if expr == 'exit()':
            break
        elif expr == ':program':
            prgm = store_program()
            execute_program(prgm)
        elif expr == 'this':
            print(env.frames)
        elif is_statement(expr):
            execute_statement(expr, env)
        else:
            print(literal(eval_parentheses(expr, env)))

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
    
def evaluate_expression(expr, env):
    """
    Evaluates an expression by converting it to an AST
    and evaluating individual operators at certain indices.
    """
    ast = AST(expr)
    tokens = ast.parse()
    indices = ast.collapse_indices(ast.build_indices())
    for idx in indices:
        op = tokens[idx]
        if idx > 0:
            left = convert_value(tokens[idx-1], env)
        else:
            left = None
        right = convert_value(tokens[idx+1], env)
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
    if len(tokens) != 1:
        throw_exception('ExprEval', str(tokens) + ' cannot be converted into a single value')
    else:
        return convert_value(tokens[0], env)
        
def eval_parentheses(expr, env):
    """
    Recursively evaluates expressions enclosed in parentheses,
    which change the order-of-operations for the expression.
    """
    def find_matching(expr):
        """
        Finds the first unmatched closing parenthesis
        returns -1 when there is no matching parenthesis.
        """
        num_open = 0
        i = 0
        for char in expr:
            if char == '(':
                num_open += 1
            elif char == ')':
                if num_open == 0:
                    return i + 1
                else:
                    num_open -= 1
            i += 1
        return -1
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

def main():
    """Main function - includes tests and runs the REPL."""
    if len(sys.argv) > 1:
        # Run a program from a text file:
        file_name = sys.argv[1]
        try:
            execute_program(file_to_str(file_name))
        except IOError:
            print("Could not read file: " + file_name)
        exit()
    env = Environment()
    execute_statement('x = 3', env)
    execute_statement('x+=7', env)
    execute_statement('y=9.23', env)
    env.new_frame()
    execute_statement('x = 5', env)
    print(env.frames)
    execute_statement('z="hello world"', env)
    execute_statement('z +="!!!"', env)
    execute_statement('a= `gelatin`', env)
    print(env.frames)
    ast = AST("3*4+5 ^ 7")
    print(ast.parse())
    print(ast.collapse_indices(ast.build_indices()))
    ast = AST("18+15*9:3+10")
    print(ast.parse())
    print(ast.collapse_indices(ast.build_indices()))

    print(evaluate_expression('1+2+3+4', Environment()))
    print(evaluate_expression('45+7*8', Environment()))
    print(evaluate_expression('3.2+18^2-7', Environment()))
    print(evaluate_expression('1:2 + 1:3 + 1:5', Environment()))
    print(evaluate_expression('2:3 + 3^3 - 1:5', Environment()))
    print(evaluate_expression('1234', Environment()))
    
    ast = AST("3 + 1 == 4")
    print(ast.parse())
    ast = AST("3 + 1 > 4")
    print(ast.parse())
    ast = AST("18:1 != 18.2")
    print(ast.parse())
    ast = AST("x = 4")
    print(ast.parse())
    ast = AST("y = 3 > 4")
    print(ast.parse())
    
    env2 = Environment()
    execute_statement('x = 3+5*4', env2)
    execute_statement('y = x + 19 - 3*6', env2)
    print(env2.frames)
    
    repl()
        
if __name__ == "__main__":
    main()
