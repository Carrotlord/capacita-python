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
    try:
        return int(val)
    except ValueError:
        try:
            return float(val)
        except ValueError:
            return None

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
        
main()