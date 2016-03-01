# Use Python 2, not Python 3

import re

test_code = """
x = 5
y = 15
x += y
"""

operators = ['+=', '=']

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
                tokens.append(buffer)
                tokens.append(c)
                buffer = ''
            else:
                buffer += c
        tokens.append(buffer)
        return tokens
    
    def build_indices(self):
        # TODO: consider modification of index as expression is being parsed.
        tokens = self.parse()
        table = [[], [], [], []]
        i = 0
        for token in tokens:
            if token in self.precedences:
                table[self.precedences[token] - 1].append(i)
            i += 1
        return table

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
        env.assign(tokens[0], convert_value(tokens[2], env))
    elif tokens[1] == '+=':
        val = env.get(tokens[0])
        env.update(tokens[0], val + convert_value(tokens[2], env))
    
def convert_value(val, env):
    """
    Given a value in string form, converts to an int, float, etc.
    """
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

def repl():
    pass

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
    print(ast.build_indices())
        
main()