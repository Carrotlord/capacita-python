test_code = """
x = 5
y = 15
x += y
"""

operators = ['+=', '=']

# TODO: finish this function
def tokenize_statement(stmt):
    tokens = []
    for i in range(len(stmt)):
        for op in operators:
            if stmt[i:i+len(op)] == op:
                tokens.append([
                    stmt[0:i].strip(),
                    op,
                    stmt[i+len(op):].strip()
                ])
                break
    return tokens

class Environment(object):
    def __init__(self):
        self.frames = [{}]
    
    def new_frame(self):
        self.frames.append({})
    
    def assign(self, var_name, value):
        self.frames[-1][var_name] = value
        
    def pop(self):
        return self.frames.pop()

def main():
    env = Environment()
    env.assign('g', 3)
    env.new_frame()
    env.assign('h', 15)
    print(env.frames)
    print(tokenize_statement("x=3"))
    print(tokenize_statement("y += 56"))
        
main()