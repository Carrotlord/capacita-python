# Use Python 2, not Python 3
# @author Jiangcheng Oliver Chu

import re
import sys
from fractions import Fraction

operators = ['+=', '=']

def file_to_str(file_name):
    """Returns contents of a text file as a string."""
    file_obj = open(file_name, 'r')
    contents = file_obj.read()
    file_obj.close()
    return contents

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
            '>': 5, '<': 5,
            ' and ': 6, ' or ': 6, ' xor ': 6
        }
        # Longer operators should be detected before shorter ones:
        self.ordered_ops = [' and ', ' or ', ' xor ',
                            '>=', '<=', '!=', '==', '<', '>',
                            '+', '-', '*', '/', '^', ':']
    
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
            for op in self.ordered_ops:
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
        table = [[], [], [], [], [], []]
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

def display(obj, use_newline=True):
    """
    Implementation of print functionality. Strings will not be printed with
    surrounding quotes, while other objects are printed as-is.
    """
    if type(obj) is str and len(obj) >= 2 and obj[0] == '"' and obj[-1] == '"':
        if use_newline:
            print(obj[1:-1])
        else:
            sys.stdout.write(obj[1:-1])
    else:
        if use_newline:
            print(literal(obj))
        else:
            sys.stdout.write(str(literal(obj)))
        
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

def prepare_control_flow(lines):
    """
    Converts if-statements, while-statements, for-statements, etc.
    into :cond and jump directives
    (:j for unconditional jump,
     :jt for jump true, and :jf for jump false).

    e.g.
    x = 100
    if x > 0
        // do something
    else
        // do other thing
    end

    0: x = 100
    1: :cond x > 0
    2: :jf 5
    3: // do something
    4: :j 6
    5: // do other thing
    6: 
    """
    def find_next_end_else(lines, start, end_only=False):
        """
        Returns the corresponding end-statement or else-statement
        for the given clause-opener (which can be an if-statement,
        while-statement, etc.)
        Skips over end and else statements that are part of nested clauses.
        If end_only is set to True, all else statements are passed over.
        """
        i = start
        open_clauses = 0
        openers = ['if ', 'while ', 'for ', 'repeat ', 'switch ']
        while i < len(lines):
            line = lines[i]
            if line == 'end':
                if open_clauses == 0:
                    return ['end', i]
                else:
                    open_clauses -= 1
            elif (not end_only) and line == 'else' and open_clauses == 0:
                return ['else', i]
            else:
                for opener in openers:
                    if line.startswith(opener):
                        open_clauses += 1
                        break
            i += 1
        throw_exception('NoEndStatement', 'Corresponding end statement does not exist.')
    def replace_labels(lines):
        """
        Replaces labels in jump directives with the actual
        addresses being jumped to.
        """
        label_table = {}
        i = 0
        for line in lines:
            if line.startswith(':label'):
                label_table[line[6:]] = i
                # Erase the label at this line:
                lines[i] = ''
            i += 1
        i = 0
        jumps = [':j ', ':jt ', ':jf ']
        for line in lines:
            for jump in jumps:
                if line.startswith(jump + 'label'):
                    label_num = line[len(jump) + 5:]
                    if label_num in label_table:
                        lines[i] = jump + str(label_table[label_num])
                        break
            i += 1
        return lines
    def prepare_else_ifs(lines):
        """
        Splits else-if statements into two separate lines:
        else followed by an if.
        Adds additional end statements for padding.
        This allows else-if statements to be evaluated using
        only basic if-else logic. For example, the following
        structures are equivalent:
        
        x = 2
        if x == 1
            A
        else if x == 2
            B
        else
            C
        end
        
        x = 2
        if x == 1
            A
        else
            if x == 2
                B
            else
                C
            end
        end
        """
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith('if '):
                # Find the end statement:
                _, end = find_next_end_else(lines, i + 1, True)
                j = i + 1
                # Keep track of how many else-ifs were split:
                splits = 0
                while j < end:
                    other_line = lines[j]
                    if other_line.startswith('else if '):
                        lines[j : j+1] = ['else', other_line[5:]]
                        end += 1
                        splits += 1
                    j += 1
                # Add extra end statements:
                lines[end : end+1] = ['end' for _ in xrange(splits + 1)]
            i += 1
        return lines
    lines = prepare_else_ifs(lines)
    i = 0
    label_counter = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('when '):
            lines[i : i+1] = [':cond ' + line[5:], ':jf ' + str(i + 3)]
        elif line.startswith('if '):
            lines[i : i+1] = [':cond ' + line[3:], ':jf label' + str(label_counter)]
            # Find the next else or end statement:
            kind, j = find_next_end_else(lines, i + 2)
            if kind == 'end':
                lines[j] = ':label' + str(label_counter)
            else:
                # kind must be an else statement.
                # replace the else statement with a jump:
                else_label = ':label' + str(label_counter)
                label_counter += 1
                lines[j : j+1] = [':j label' + str(label_counter), else_label]
                kind, end = find_next_end_else(lines, j + 1)
                if kind == 'else':
                    throw_exception('MultipleElseStatement',
                                    'if statements cannot have multiple else clauses'
                                    ' (aside from else-if statements).')
                lines[end] = ':label' + str(label_counter)
            label_counter += 1
        i += 1
    lines = replace_labels(lines)
    return lines

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

# TODO: finish this function
def tokenize_statement(stmt):
    """
    Tokenizes a statement based on keywords and assignment operators.
    e.g. 'print 2+2' -> ['print', '2+2']
         'x += 5 * 6'    -> ['x', '+=', '5 * 6']
    """
    if stmt.startswith('print '):
        return ['print', stmt[6:]]
    elif stmt.startswith('show '):
        return ['show', stmt[5:]]
    elif stmt.startswith(':cond '):
        return [':cond', stmt[6:]]
    elif stmt.startswith(':j '):
        return [':j', stmt[3:]]
    elif stmt.startswith(':jf '):
        return [':jf', stmt[4:]]
    elif stmt.startswith(':jt '):
        return [':jt', stmt[4:]]
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
