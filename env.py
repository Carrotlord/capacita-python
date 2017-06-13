from exception import throw_exception
from builtin_function import int_div, make_list

class Environment(object):
    """
    A list of frames containing key-value pairs representing variable names
    bound to their values.
    """
    def __init__(self):
        self.frames = [{'null': None, 'true': True, 'false': False,
                        'intDiv': int_div, 'makeList': make_list}]
    
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

    def merge_latest(self, other_env):
        latest_frame = other_env.frames[-1]
        for var, value in latest_frame.items():
            self.assign(var, value)
            
    def copy(self):
        """
        Provides a deep copy of the current environment.
        """
        new_env = Environment()
        new_frames = []
        for frame in self.frames:
            new_frames.append({k: v for k, v in frame.items()})
        new_env.frames = new_frames
        return new_env

    def __repr__(self):
        return str(self.frames)

    def __str__(self):
        return repr(self)
