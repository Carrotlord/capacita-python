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
from prepare_program import prepare_program
from execution import execute_statement, \
                      evaluate_expression, \
                      execute_lines, \
                      eval_parentheses, \
                      is_statement
from function import extract_functions

def execute_program(prgm):
    """Executes a program given as a string."""
    prgm, env = extract_functions(prgm)
    lines = prepare_program(prgm)
    execute_lines(lines, env)
    
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

def main():
    """Main function - includes tests and runs the REPL."""
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        if first_arg == '--test':
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
        elif first_arg == '--test2':
            ast = AST('x = "ice cream, eggs, and milk" + "...alpha or beta"')
            print(ast.parse())
            ast = AST('y = f(1 + 1, 2 + 2, 3 + 3) - g((9+7)*2, 128/(2+2))')
            print(ast.parse())
            ast = AST('z = f("ice cream", "eggs and milk") * g("alpha or beta", 3:8, "gamma or delta")')
            print(ast.parse())
            ast = AST('makeList(1,2,3) + makeList(4,5,6)')
            print(ast.parse())
        else:
            # Run a program from a text file:
            file_name = first_arg
            try:
                execute_program(file_to_str(file_name))
            except IOError:
                print("Could not read file: " + file_name)
        exit()
    repl()
        
if __name__ == "__main__":
    main()
