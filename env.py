from exception import throw_exception
from builtin_function import int_div, make_list
from execution import eval_parentheses
from type_tree import value_is_a

import re

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
        # Check for a type restriction
        match_obj = re.match(r'([A-Za-z_][A-Za-z_0-9]*) (\$?[A-Za-z_][A-Za-z_0-9]*)', var_name)
        if match_obj:
            kind = match_obj.group(1)
            if not value_is_a(value, kind):
                throw_exception('MismatchedType', str(value) + ' is not of type ' + kind)
            var = match_obj.group(2)
            if var in self.frames[-1]:
                type_tuple = self.frames[-1][var]
                if type(type_tuple) is tuple:
                    existing_kind = type_tuple[0]
                    if kind != existing_kind:
                        throw_exception('AlreadyRestrictedType', var + ' already has type ' + existing_kind)
                else:
                    throw_exception('AlreadyAnyType',
                        var + ' already has type Any and cannot be further restricted.')
            self.frames[-1][var] = (kind, value)
        else:
            # Is this an assignment to an index?
            match_obj = re.match(r'(\$?[A-Za-z_][A-Za-z_0-9]*)\[(.+)\]', var_name)
            if match_obj:
                indexable = match_obj.group(1)
                index = eval_parentheses(match_obj.group(2), self)
                container = self.frames[-1][indexable]
                if type(container) is tuple:
                    # Modify the iterable contained within the tuple
                    iterable = container[1]
                    iterable[index] = value
                else:
                    # This iterable has no type restriction
                    self.frames[-1][indexable][index] = value
            else:
                if var_name in self.frames[-1] and type(self.frames[-1][var_name]) is tuple:
                    # There is an existing type restriction
                    kind = self.frames[-1][var_name][0]
                    if not value_is_a(value, kind):
                        throw_exception('MismatchedType', str(value) + ' is not of type ' + kind)
                    self.frames[-1][var_name] = (kind, value)
                else:
                    # There is no type restriction given
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
                value = self.frames[i][var_name]
                if type(value) is tuple:
                    return value[1]
                return value
            else:
                i -= 1
        throw_exception('UndefinedVariable', var_name + ' is not defined.')
        
    def has_name(self, var_name):
        i = -1
        while i >= -len(self.frames):
            if var_name in self.frames[i]:
                return True
            else:
                i -= 1
        return False
        
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
