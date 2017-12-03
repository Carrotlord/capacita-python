from ratio import Ratio
from exception import throw_exception

class TypeTree(object):
    def __init__(self, *names):
        self.names = names
        self.subclasses = []
    
    def add_subclass(self, subclass):
        self.subclasses.append(subclass)
    
    def has_name(self, name):
        return name in self.names
    
    def has_child(self, name):
        for subclass in self.subclasses:
            if subclass.has_name(name) or subclass.has_child(name):
                return True
        return False
    
    def categorizes(self, name):
        """
        Returns True if this type categorizes name.
        
        e.g. If this type is Number, should return True
        if name is 'Int' or 'Double', and False if name
        is 'String' or 'List'.
        """
        return self.has_name(name) or self.has_child(name)

def get_type(value):
    kind = type(value)
    if kind is int:
        return 'Int'
    elif kind is float:
        return 'Double'
    elif kind is bool:
        return 'Boolean'
    elif kind is str:
        return 'String'
    elif kind is list:
        return 'List'
    if value.__class__ is Ratio:
        return 'Ratio'
    elif value is None:
        return 'Null'
    elif str(value).startswith('<function'):
        return 'Function'
    throw_exception('UnknownType', str(value) + ' has an unknown type.')
    
def generate_default_tree():
    integers = TypeTree('Int', 'Integer')
    doubles = TypeTree('Double')
    bools = TypeTree('Boolean')
    strs = TypeTree('String')
    lists = TypeTree('List')
    ratios = TypeTree('Ratio', 'Rational')
    nulls = TypeTree('Null', 'Void')
    functions = TypeTree('Function')
    
    numbers = TypeTree('Number')
    numbers.add_subclass(integers)
    numbers.add_subclass(doubles)
    numbers.add_subclass(ratios)
    
    sequences = TypeTree('Sequence', 'Iterable')
    sequences.add_subclass(strs)
    sequences.add_subclass(lists)
    
    objects = TypeTree('Object')
    objects.add_subclass(numbers)
    objects.add_subclass(sequences)
    objects.add_subclass(bools)
    objects.add_subclass(nulls)
    objects.add_subclass(functions)
    
    return {
        'Int': integers,
        'Integer': integers,
        'Double': doubles,
        'Boolean': bools,
        'String': strs,
        'List': lists,
        'Ratio': ratios,
        'Rational': ratios,
        'Null': nulls,
        'Void': nulls,
        'Function': functions,
        'Number': numbers,
        'Sequence': sequences,
        'Iterable': sequences,
        'Object': objects
    }
