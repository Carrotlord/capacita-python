# Use Python 2, not Python 3
# @author Jiangcheng Oliver Chu

import re
from fractions import Fraction

test_code = """
x = 5
y = 15
x += y
"""

operators = ['+=', '=']

def frac_to_ratio(frac):
    """Convert Python fraction object to Ratio."""
    try:
        return Ratio(frac.numerator, frac.denominator)
    except AttributeError:
        return frac
    
def prepare_frac(ratio):
    """Convert Ratio objects back to Python fraction."""
    if ratio.__class__ is Ratio:
        return ratio.fraction
    return ratio

class Ratio(object):
    """Fraction object printed as numerator:denominator."""
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
    
    def __float__(self):
        return float(self.fraction.numerator) / self.fraction.denominator
        
    def __eq__(self, other):
        return float(self) == float(other)
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
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
        """Setup expression and precedences of operators."""
        self.expr = expr
        self.precedences = {
            ':': 1,
            '^': 2,
            '*': 3, '/': 3,
            '+': 4, '-': 4,
            '==': 5, '!=': 5, '>=': 5, '<=': 5,
            '>': 5, '<': 5
        }
    
    def weakest(self):
        """
        Returns the integer precedence of the most weakly binding
        operator in self.expr.
        """
        current = 0
        result = None
        for op in self.expr:
            if op in self.precedences and self.precedences[op] > current:
                current = self.precedences[op]
                result = op
        return result
        
    def parse(self):
        """
        Splits an expression based on its operators.
        e.g. '2 + 3*4' -> ['2', '+', '3', '*', '4']
        """
        buffer = ''
        tokens = []
        expr_length = len(self.expr)
        i = 0
        while i < expr_length:
            op_detected = False
            for op in self.precedences:
                op_length = len(op)
                if self.expr[i : i+op_length] == op:
                    buffer_contents = buffer.strip()
                    if len(buffer_contents) > 0:
                        tokens.append(buffer_contents)
                    tokens.append(op)
                    buffer = ''
                    i += op_length
                    op_detected = True
                    break
            if not op_detected:
                buffer += self.expr[i]
                i += 1
        buffer_contents = buffer.strip()
        if len(buffer_contents) > 0:
            tokens.append(buffer_contents)
        return self.merge_negatives(tokens)
    
    def merge_negatives(self, tokens):
        """
        Allows for proper expression of the unary operator '-'
        e.g. ['-', '233', '+', '-', '18', ':', '-', '1']
             -> ['-233', '+', '-18', ':', '-1']
        """
        if len(tokens) <= 1:
            return tokens
        if tokens[0] == '-' and is_positive_numeric(tokens[1]):
            return self.merge_negatives(['-' + str(tokens[1])] + tokens[2:])
        i = 0
        max_len = len(tokens) - 2
        while i < max_len:
            if tokens[i] in self.precedences and tokens[i + 1] == '-' and \
               is_positive_numeric(tokens[i + 2]):
                tokens[i+1 : i+3] = ['-' + str(tokens[i + 2])]
                max_len = len(tokens) - 2
            i += 1
        return tokens
    
    def build_indices(self):
        """
        Takes a list of tokens and collects indices of operators
        based on their precedence. The first index encountered indicates
        which operators should be evaluated first.
        e.g. '1+1+3*4^7' -> ['1', '+', '1', '+', '3', '*', '4', '^', '7']
                   indices:   0    1    2    3    4    5    6    7    8
             -> [[], [7], [5], [1, 3]]
        """
        tokens = self.parse()
        table = [[], [], [], [], []]
        i = 0
        for token in tokens:
            if token in self.precedences:
                table[self.precedences[token] - 1].append(i)
            i += 1
        return table
    
    def collapse_indices(self, index_table):
        """
        Given a table of indices, determines which 'final' index
        the operators will be at during each stage of simplification.
        e.g. [[], [7], [5], [1, 3]]
          -> [7, 5, 1, 3]
          -> [7, 5, 1, 1]
        Notice the last index was shifted to the left by 2 thanks
        to the simplification that occurred previously.
        """
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

def display(obj):
    """
    Implementation of print functionality. Strings will not be printed with
    surrounding quotes, while other objects are printed as-is.
    """
    if type(obj) is str and len(obj) >= 2 and obj[0] == '"' and obj[-1] == '"':
        print(obj[1:-1])
    else:
        print(literal(obj))
        
def literal(obj):
    """
    Returns a string representation of the object as a Capacita literal.
    Similiar to Python's repr(...) function.
    """
    if obj is True:
        return 'true'
    elif obj is False:
        return 'false'
    elif obj is None:
        return 'null'
    else:
        return obj

def execute_program(prgm):
    """Executes a program given as a string."""
    lines = prgm.split('\n')
    env = Environment()
    for line in lines:
        execute_statement(line, env)

# TODO: finish this function
def tokenize_statement(stmt):
    """
    Tokenizes a statement based on keywords and assignment operators.
    e.g. 'print 2+2' -> ['print', '2+2']
         'x += 5 * 6'    -> ['x', '+=', '5 * 6']
    """
    if stmt.startswith('print '):
        return ['print', stmt[6:]]
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
    """Executes a statement in a given environment."""
    if len(stmt.strip()) == 0:
        return
    tokens = tokenize_statement(stmt)
    if tokens[0] == 'print':
        display(eval_parentheses(tokens[1], env))
    elif tokens[1] == '=':
        env.assign(tokens[0], eval_parentheses(tokens[2], env))
    elif tokens[1] == '+=':
        val = env.get(tokens[0])
        env.update(tokens[0], plus(val, eval_parentheses(tokens[2], env)))
    
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

def is_numeric(val):
    """
    Returns True if val is an integer or float, else False.
    """
    try:
        int(val)
    except ValueError:
        try:
            float(val)
        except ValueError:
            return False
        else:
            return True
    else:
        return True

def is_positive_numeric(val):
    """
    Returns True if val is a positive integer or float, else False.
    """
    if not is_numeric(val):
        return False
    val = str(val)
    if len(val) > 0 and val[0] == '-':
        return False
    return True
            
class Ribbon(object):
    """
    A linked-list of characters, presented as an alternative to the
    string type.
    """
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
    """
    Throws a Capacita exception and exits the program.
    """
    print(kind + ' exception')
    print(msg)
    exit()

class Environment(object):
    """
    A list of frames containing key-value pairs representing variable names
    bound to their values.
    """
    def __init__(self):
        self.frames = [{'null': None, 'true': True, 'false': False}]
    
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
    """Returns True if query is a statement, else False."""
    if query.startswith('print '):
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
