test_code = """
x = 5
y = 15
x += y
"""

class Environment(object):
    def __init__(self):
        self.frames = []
    
    def new_frame(self):
        self.frames.append({})
    
    def assign(self, var_name, value):
        self.frames[var_name] = value
        
    def pop(self):
        return self.frames.pop()
    