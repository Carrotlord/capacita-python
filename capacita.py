# Use Python 2, not Python 3

import re
from fractions import Fraction

test_code = """
x = 5
y = 15
x += y
"""

operators = ['+=', '=']

def frac_to_ratio(frac):
    return Ratio(frac.numerator, frac.denominator)
    
def prepare_frac(ratio):
    if type(ratio) is Ratio:
        return ratio.fraction
    return ratio

class Ratio(object):
    def __init__(self, n, d):
        self.fraction = Fraction(n, d)
        
    def __add__(self, other):
        return frac_to_ratio(self.fraction + prepare_frac(other))
    
    def __sub__(self, other):
        return frac_to_ratio(self.fraction - prepare_frac(other))
        
    def __mul__(self, other):
        return frac_to_ratio(self.fraction * prepare_frac(other))
        
    def __div__(self, other):
        return frac_to_ratio(self.fraction / prepare_frac(other))
    
    def __pow__(self, other):
        return frac_to_ratio(self.fraction ** prepare_frac(other))
    
    def __repr__(self):
        return str(self.fraction.numerator) + ':' + str(self.fraction.denominator)
    
    def __str__(self):
        return repr(self)

class AST(object):
    """
    Abstract syntax tree with strongly binding operators at the bottom.
    The smaller the precedence, the stronger the binding.
    """
    def __init__(self, expr):
        self.expr = expr
        self.precedences = {
            ':': 1,
            '^': 2,
            '*': 3, '/': 3,
            '+': 4, '-': 4
        }
        self.left_child = None
        self.right_child = None
        self.op = None
    
    def weakest(self):
        current = 0
        result = None
        for op in self.expr:
            if op in self.precedences and self.precedences[op] > current:
                current = self.precedences[op]
                result = op
        return result
        
    def parse(self):
        buffer = ''
        tokens = []
        for c in self.expr:
            if c in self.precedences:
                tokens.append(buffer.strip())
                tokens.append(c)
                buffer = ''
            else:
                buffer += c
        tokens.append(buffer.strip())
        return tokens
    
    def build_indices(self):
        tokens = self.parse()
        table = [[], [], [], []]
        i = 0
        for token in tokens:
            if token in self.precedences:
                table[self.precedences[token] - 1].append(i)
            i += 1
        return table
    
    def collapse_indices(self, index_table):
        all = []
        for index_list in index_table:
            all += index_list
        i = 0
        for index in all:
            j = i + 1
            for checked_index in all[i+1:]:
                # Indices that are greater than
                # the current should be moved over 2 slots:
                if index < checked_index:
                    all[j] -= 2
                j += 1
            i += 1
        return all
        

# TODO: finish this function
def tokenize_statement(stmt):
    for i in range(len(stmt)):
        for op in operators:
            if stmt[i:i+len(op)] == op:
                return [
                    stmt[0:i].strip(),
                    op,
                    stmt[i+len(op):].strip()
                ]
    return []
    
def execute_statement(stmt, env):
    tokens = tokenize_statement(stmt)
    if tokens[1] == '=':
        env.assign(tokens[0], evaluate_expression(tokens[2], env))
    elif tokens[1] == '+=':
        val = env.get(tokens[0])
        env.update(tokens[0], val + evaluate_expression(tokens[2], env))
    
def convert_value(val, env):
    """
    Given a value in string form, converts to an int, float, etc.
    Or, given a variable name, retrieves the value of that variable.
    """
    if type(val) is not str:
        return val
    if re.match('[A-Za-z_][A-Za-z_0-9]*', val):
        # Grab a variable's value:
        return env.get(val)
    if len(val) >= 2:
        if val[0] == "'" and val[-1] == "'":
            return val[1:-1]
        elif val[0] == '"' and val[-1] == '"':
            return val[1:-1]
        elif val[0] == '`' and val[-1] == '`':
            return Ribbon(val[1:-1])
    try:
        return int(val)
    except ValueError:
        try:
            return float(val)
        except ValueError:
            return None
            
class Ribbon(object):
    def __init__(self, string):
        if len(string) == 0:
            self.char = None
            self.rest = None
        else:
            self.char = string[0]
            self.rest = Ribbon(string[1:])
    
    def to_string(self):
        if self.char == None:
            return ''
        string = self.char
        next = self.rest
        while next.char:
            string += next.char
            next = next.rest
        return string
    
    def __repr__(self):
        return '`' + self.to_string() + '`'
    
    def __str__(self):
        return repr(self)
        
def throw_exception(kind, msg):
    print(kind + ' exception')
    print(msg)
    exit()

class Environment(object):
    def __init__(self):
        self.frames = [{}]
    
    def new_frame(self):
        self.frames.append({})
    
    def assign(self, var_name, value):
        self.frames[-1][var_name] = value
    
    def update(self, var_name, value):
        if var_name in self.frames[-1]:
            self.frames[-1][var_name] = value
        else:
            throw_exception('UndefinedVariable', var_name + ' is not defined.')
        
    def get(self, var_name):
        i = -1
        while i >= -len(self.frames):
            if var_name in self.frames[i]:
                return self.frames[i][var_name]
            else:
                i -= 1
        throw_exception('UndefinedVariable', var_name + ' is not defined.')
        
    def pop(self):
        return self.frames.pop()
        
def is_statement(query):
    # TODO : need more robust testing of statement vs expression
    return '=' in query

def repl():
    env = Environment()
    while True:
        expr = raw_input('Capacita> ')
        expr = expr.strip()
        if expr == 'exit()':
            break
        elif expr == 'this':
            print(env.frames)
        elif is_statement(expr):
            execute_statement(expr, env)
        else:
            print(evaluate_expression(expr, env))
    
def evaluate_expression(expr, env):
    ast = AST(expr)
    tokens = ast.parse()
    indices = ast.collapse_indices(ast.build_indices())
    for idx in indices:
        op = tokens[idx]
        if op == '+':
            tokens[idx-1 : idx+2] = [convert_value(tokens[idx-1], env) + \
                                     convert_value(tokens[idx+1], env)]
        elif op == '-':
            tokens[idx-1 : idx+2] = [convert_value(tokens[idx-1], env) - \
                                     convert_value(tokens[idx+1], env)]
        elif op == '*':
            tokens[idx-1 : idx+2] = [convert_value(tokens[idx-1], env) * \
                                     convert_value(tokens[idx+1], env)]
        elif op == '/':
            tokens[idx-1 : idx+2] = [float(convert_value(tokens[idx-1], env)) / \
                                     float(convert_value(tokens[idx+1], env))]
        elif op == '^':
            tokens[idx-1 : idx+2] = [convert_value(tokens[idx-1], env) ** \
                                     convert_value(tokens[idx+1], env)]
        elif op == ':':
            tokens[idx-1 : idx+2] = [Ratio(convert_value(tokens[idx-1], env), \
                                     convert_value(tokens[idx+1], env))]
    if len(tokens) != 1:
        throw_exception('ExprEval', str(tokens) + ' cannot be converted into a single value')
    else:
        return convert_value(tokens[0], env)

def main():
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
    
    env2 = Environment()
    execute_statement('x = 3+5*4', env2)
    execute_statement('y = x + 19 - 3*6', env2)
    print(env2.frames)
    
    repl()
        
main()