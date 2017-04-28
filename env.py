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
