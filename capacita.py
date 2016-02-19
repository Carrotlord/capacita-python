# Use Python 2, not Python 3

test_code = """
x = 5
y = 15
x += y
"""

operators = ['+=', '=']

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
        env.assign(tokens[0], convert_value(tokens[2]))
    elif tokens[1] == '+=':
        val = env.get(tokens[0])
        env.assign(tokens[0], val + convert_value(tokens[2]))
    
def convert_value(val):
    """
    Given a value in string form, converts to an int, float, etc.
    """
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

class Environment(object):
    def __init__(self):
        self.frames = [{}]
    
    def new_frame(self):
        self.frames.append({})
    
    def assign(self, var_name, value):
        self.frames[-1][var_name] = value
        
    def get(self, var_name):
        return self.frames[-1][var_name]
        
    def pop(self):
        return self.frames.pop()

def main():
    env = Environment()
    execute_statement('x = 3', env)
    execute_statement('x+=7', env)
    execute_statement('y=9.23', env)
    print(env.frames)
    execute_statement('z="hello world"', env)
    execute_statement('z +="!!!"', env)
    execute_statement('a= `gelatin`', env)
    print(env.frames)
        
main()