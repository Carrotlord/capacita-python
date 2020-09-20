# Use Python 2, not Python 3
# @author Jiangcheng Oliver Chu

import re
import sys

from ratio import Ratio
from ast2 import AST
from control_flow import prepare_control_flow, openers
from ribbon import Ribbon
from tokens import tokenize_statement
from fileio import file_to_str
from exception import throw_exception

import tests
import env as environment
import execution
import function
import prepare_program
import console
import line_manager

def execute_file(file_name, existing_env=None):
    if existing_env is None:
        existing_env = environment.Environment()
    file_name = existing_env.set_correct_directory(file_name)
    if not existing_env.is_already_imported(file_name):
        existing_env.add_import(file_name)
        try:
            execute_program(file_to_str(file_name), existing_env)
        except IOError:
            print('Could not read file: ' + file_name)

def convert_program_to_lines(prgm, existing_env=None):
    prgm = prepare_program.preprocess(prgm)
    line_mgr, env, _ = function.extract_functions(prgm, existing_env)
    prepare_program.prepare_program(line_mgr)
    return line_mgr, env

def execute_program(prgm, existing_env=None):
    """Executes a program given as a string."""
    line_mgr, env = convert_program_to_lines(prgm, existing_env)
    execution.execute_lines(line_mgr, env)
    
def store_program(get_input):
    """
    Stores a program line-by-line until :end statement is reached.
    """
    lines = ""
    next_line = None
    while True:
        next_line = get_input()
        if next_line == ':end':
            break
        lines += next_line + '\n'
    return lines

def make_indentation(num_open_clauses):
    indentation = max(0, 4 * (num_open_clauses - 1))
    return ' ' * indentation

def store_code_block(get_input, first_line, brace_matcher, prompt='Capacita* '):
    """
    Stores a code block line-by-line until all clauses have been closed.
    """
    if first_line.startswith('when '):
        return first_line + '\n' + get_input(prompt + '    ')
    if is_clause_opener(first_line):
        open_clauses = 1
        lines = first_line + '\n'
    else:
        open_clauses = 0
        lines = first_line
    while open_clauses > 0 or not brace_matcher.is_complete():
        next_line = get_input(prompt + make_indentation(open_clauses)).strip()
        brace_matcher.match_line(next_line)
        if next_line == 'end':
            open_clauses -= 1
        elif is_clause_opener(next_line):
            open_clauses += 1
        if brace_matcher.is_complete():
            lines += next_line + '\n'
        else:
            # Glue lines together during brace matching
            lines += next_line
    return lines

def is_clause_opener(line):
    if line == 'try' or line.startswith('class '):
        return True
    for opener in openers:
        if line.startswith(opener):
            return True
    return False

def print_evaluated_expr(expr, env):
    print(console.literal(execution.eval_parentheses(expr, env)))

def repl(existing_env=None, get_input=None):
    """
    Read-eval-print loop. Whole programs can be run by using
    the ':program' directive, ending with ':end'.
    Use the 'this' keyword to see the current environment frames.
    """
    if existing_env is None:
        env = environment.Environment()
    else:
        env = existing_env
    if get_input is None:
        get_input = raw_input
    brace_matcher = prepare_program.BraceMatcher()
    while True:
        brace_matcher.reset()
        expr = get_input('Capacita> ')
        expr = expr.strip()
        if expr == 'exit()':
            break
        elif len(expr) == 0:
            continue
        elif expr == ':program':
            prgm = store_program(get_input)
            execute_program(prgm)
        elif expr == ':code':
            prgm = store_program(get_input)
            execute_program(prgm, env)
        elif expr.startswith('when ') or is_clause_opener(expr) or \
             not brace_matcher.match_line(expr).is_complete():
            prgm = store_code_block(get_input, expr, brace_matcher)
            if prgm.rstrip('\n').count('\n') == 0 and \
               not line_manager.is_statement(prgm):
                print_evaluated_expr(prgm, env)
            else:
                execute_program(prgm, env)
        elif expr == 'this':
            print(env.frames)
        else:
            # Since expr could contain semicolon-separated lines of code,
            # extract all the lines:
            line_mgr, _ = convert_program_to_lines(expr)
            line_mgr.classify_statements()
            if len(line_mgr) > 1:
                leading_lines = line_mgr[:-1]
                execution.execute_lines(leading_lines, env)
            last_expr_data = line_mgr.get_line_data(-1)
            last_expr = last_expr_data.line
            if last_expr_data.is_statement:
                execution.execute_statement(last_expr_data, False, env)
            else:
                print_evaluated_expr(last_expr, env)

def main():
    """Main function - includes tests and runs the REPL."""
    argc = len(sys.argv)
    if argc > 1:
        first_arg = sys.argv[1]
        if first_arg == '--test':
            env = environment.Environment()
            execution.execute_statement('x = 3', env)
            execution.execute_statement('x+=7', env)
            execution.execute_statement('y=9.23', env)
            env.new_frame()
            execution.execute_statement('x = 5', env)
            print(env.frames)
            execution.execute_statement('z="hello world"', env)
            execution.execute_statement('z +="!!!"', env)
            execution.execute_statement('a= `gelatin`', env)
            print(env.frames)
            ast = AST("3*4+5 ^ 7")
            print(ast.parse())
            print(ast.collapse_indices(ast.build_indices()))
            ast = AST("18+15*9:3+10")
            print(ast.parse())
            print(ast.collapse_indices(ast.build_indices()))

            print(execution.evaluate_expression('1+2+3+4', environment.Environment()))
            print(execution.evaluate_expression('45+7*8', environment.Environment()))
            print(execution.evaluate_expression('3.2+18^2-7', environment.Environment()))
            print(execution.evaluate_expression('1:2 + 1:3 + 1:5', environment.Environment()))
            print(execution.evaluate_expression('2:3 + 3^3 - 1:5', environment.Environment()))
            print(execution.evaluate_expression('1234', environment.Environment()))
            
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
            
            env2 = environment.Environment()
            execution.execute_statement('x = 3+5*4', env2)
            execution.execute_statement('y = x + 19 - 3*6', env2)
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
            ast = AST('[max(16, 25), max(36, max(49, 64))]')
            print(ast.parse())
            ast = AST('[concat_lists([10], [20]), concat_lists([30], [40])]')
            print(ast.parse())
        elif first_arg == '--test3':
            ast = AST('[1, 2, 3]')
            print(ast.split_list_elems())
            ast = AST('[f(2), f(3), f(4)]')
            print(ast.split_list_elems())
            ast = AST('[f(2, 3), f(3, 4, 5), f(4, 1)]')
            print(ast.split_list_elems())
            ast = AST('1 + 2 * 3')
            print(ast.split_list_elems())
            print(ast.parse())
        elif first_arg == '--test4':
            ast = AST('x.length()')
            print(ast.parse())
            ast = AST('[1,2,3].length()')
            print(ast.parse())
            ast = AST('3.01')
            print(ast.parse())
            ast = AST('3.1')
            print(ast.parse())
        elif first_arg == '--test5':
            env = environment.Environment()
            env.new_type(['Number'], 'ComplexNumber')
            c = {'$type': 'ComplexNumber', 'real': 1, 'imag': 2}
            print(env.value_is_a(c, 'ComplexNumber'))
            print(env.value_is_a(c, 'Number'))
            print(env.value_is_a(c, 'Int'))
            print("")
            env.new_type(['Object'], 'Food')
            env.new_type(['Food'], 'Pizza')
            env.new_type(['Food'], 'Dessert')
            env.new_type(['Dessert'], 'ChocolateItem')
            env.new_type(['Pizza'], 'PepperoniPizza')
            env.new_type(['Pizza', 'ChocolateItem'], 'ChocolatePizza')
            pepperoni_pizza = {'$type': 'PepperoniPizza'}
            chocolate_pizza = {'$type': 'ChocolatePizza'}
            print(env.value_is_a(pepperoni_pizza, 'PepperoniPizza'))
            print(env.value_is_a(pepperoni_pizza, 'Pizza'))
            print(env.value_is_a(pepperoni_pizza, 'Food'))
            print(env.value_is_a(pepperoni_pizza, 'Dessert'))
            print(env.value_is_a(pepperoni_pizza, 'ChocolateItem'))
            print("")
            print(env.value_is_a(chocolate_pizza, 'PepperoniPizza'))
            print(env.value_is_a(chocolate_pizza, 'Pizza'))
            print(env.value_is_a(chocolate_pizza, 'Food'))
            print(env.value_is_a(chocolate_pizza, 'Dessert'))
            print(env.value_is_a(chocolate_pizza, 'ChocolateItem'))
            print("")
            env.new_type(['ChocolatePizza'], 'HugeChocolatePizza')
            huge_chocolate_pizza = {'$type': 'HugeChocolatePizza'}
            print(env.value_is_a(huge_chocolate_pizza, 'PepperoniPizza'))
            print(env.value_is_a(huge_chocolate_pizza, 'Pizza'))
            print(env.value_is_a(huge_chocolate_pizza, 'Food'))
            print(env.value_is_a(huge_chocolate_pizza, 'Dessert'))
            print(env.value_is_a(huge_chocolate_pizza, 'ChocolateItem'))
            print(env.value_is_a(huge_chocolate_pizza, 'ChocolatePizza'))
            print("")
        elif first_arg == '--test6':
            ast = AST('{1, 2 | 3, 4}')
            print(ast.parse())
        elif first_arg == '--test7':
            ast = AST('throw "something"')
            print(ast.parse())
        elif first_arg == '--test8':
            ast = AST('true and not false')
            print(ast.parse())
            print(ast.collapse_indices(ast.build_indices()))
        elif first_arg == '--test9':
            sample = """
                x = 5 // comment
                // comment
                /* multi
                line
                comment
                */y = 6
                z = "https://example.com"
            """
            print(prepare_program.preprocess(sample))
        elif first_arg == '--test10':
            ast = AST('-3.0e5 + 186e-20 * 1e-6 / 28.8e+6 + 34.4e+99')
            print(ast.parse())
            ast = AST('-3.0E5 + 186E-20 * 1E-6 / 28.8e+6 + 34.4E+99')
            print(ast.parse())
        elif first_arg == '--test11':
            print(execution.is_assignment_statement('a = 5'))
            print(execution.is_assignment_statement('a=5==6'))
            print(execution.is_assignment_statement('not (5==6) and (8>=7)'))
            print(execution.is_assignment_statement('z='))
        elif first_arg == '--test12':
            lines = [
                'sub this + that',
                'func Int x + this',
                'func x + this',
                'func this * y',
                'func Int -this',
                'sub -this',
                'sub not this',
                'sub Boolean not this',
                'sub this-b',
                'sub b-this',
                'func Int-this',
                'func Int- this',
                'sub Int - this'
            ]
            print(prepare_program.replace_op_overload_syntax(lines))
        elif first_arg == '--test-tree-merge':
            tests.test_tree_merge()
        elif first_arg == '--test-all':
            tests.test_all('capacita_programs')
        elif first_arg == '--test-all-fast':
            tests.test_all('capacita_programs', has_delay=False)
        elif first_arg == '--test-repl':
            tests.test_all('capacita_programs', has_delay=True, use_repl=True)
        elif first_arg == '--test-repl-fast':
            tests.test_all('capacita_programs', has_delay=False, use_repl=True)
        elif first_arg == '--test-file' and argc > 2:
            if argc == 4 and sys.argv[2] == '--repl':
                tests.test_file(sys.argv[3], use_repl=True)
            else:
                tests.test_file(sys.argv[2], use_repl=False)
        else:
            # Run a program from a text file:
            file_name = first_arg
            execute_file(file_name)
        exit()
    repl()
        
if __name__ == "__main__":
    main()
