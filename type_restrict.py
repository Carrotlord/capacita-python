from exception import throw_exception

import console

def enforce_type(val, kind, env, msg=''):
    if not env.value_is_a(val, kind):
        throw_exception(
            'IncorrectTypeGiven',
            '{0} is not of type {1} {2}'.format(val, kind, msg)
        )

def is_considered_list(val):
    # A restricted list should behave like a regular list,
    # so consider them the same type
    return type(val) is list or val.__class__ is RestrictedList

class RestrictedList(object):
    def __init__(self, contents, kind, env):
        self.element_kind = kind
        self.msg = 'for a list restricted with element type {0}'.format(self.element_kind)
        # TODO : make sure storing the environment in this manner
        # does not cause issues with scoping
        self.env = env
        # Shallow copy original list, and check each element's type
        self.contents = []
        for elem in contents:
            self.enforce(elem)
            self.contents.append(elem)
    
    def enforce(self, val):
        enforce_type(val, self.element_kind, self.env, self.msg)
    
    def append(self, new_elem):
        self.enforce(new_elem)
        self.contents.append(new_elem)
    
    def __add__(self, other):
        # TODO : For restricted lists of different element types,
        # find the parent type common to both types that is most
        # specific.
        # e.g.
        # ["a", "b"] of String + [[1,2],[3.1]] of List
        # should be ["a", "b", [1,2], [3.1]] of Sequence
        # because Strings and Lists are both sequences.
        if type(other) is list:
            return self.contents + other
        else:
            return self.contents + other.contents
    
    def __radd__(self, other):
        return other + self.contents
    
    def __setitem__(self, index, new_elem):
        self.enforce(new_elem)
        self.contents[index] = new_elem
    
    def __getitem__(self, index):
        return self.contents[index]
    
    def __len__(self):
        return len(self.contents)
    
    def pop(self):
        return self.contents.pop()
        
    def __str__(self):
        return repr(self)
    
    def __repr__(self):
        return '{0} of {1}'.format(console.literal(self.contents), self.element_kind)

def type_restrict(val, type_tree, env):
    kind = type_tree.get_default_name()
    if type(val) is list:
        return RestrictedList(val, kind, env)
    else:
        throw_exception(
            'CannotTypeRestrictValue',
            'Value {0} cannot be restricted with type {1}'.format(val, kind)
        )
