from ratio import Ratio
from table import Table
from exception import throw_exception
from trigger import Trigger

class TypeTree(object):
    def __init__(self, *names):
        self.names = names
        self.subclasses = []
    
    def add_subclass(self, subclass):
        self.subclasses.append(subclass)
    
    def get_default_name(self):
        return self.names[0]

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
    
    def __repr__(self):
        return self.format()
    
    def __str__(self):
        return repr(self)
    
    def format(self, indent_size=0):
        remainder = ''
        for subclass in self.subclasses:
            remainder += subclass.format(indent_size + 2)
        return '{0}{1}\n{2}'.format(' ' * indent_size, self.names, remainder)

    def format_as_literal(self):
        formatted = self.format()
        formatted = formatted.replace('(', '\\x28').replace(')', '\\x29')
        return '"{0}"'.format(formatted)

def merge_trees(tree, other):
    """
    Combines two type trees into a single tree.
    The new tree will contain all the children of both
    original trees. Children that are shared will be
    recursively merged.
    
    e.g.
    Take the two trees:
       A        A
      / \      / \
     B   C    D   B
     |           / \
     G          E   F
    The result should be:
         A
        /|\
       B C D
      /|\
     G E F
    """
    if tree.names != other.names:
        throw_exception(
            'CannotMergeTrees',
            'Root value {0} is not the same as {1}'.format(tree.names, other.names)
        )
    combined_subclasses = {}
    for subclass in tree.subclasses:
        combined_subclasses[subclass.names] = subclass
    for subclass in other.subclasses:
        if subclass.names in combined_subclasses:
            old_tree = combined_subclasses[subclass.names]
            new_tree = merge_trees(old_tree, subclass)
            combined_subclasses[subclass.names] = new_tree
        else:
            combined_subclasses[subclass.names] = subclass
    result = TypeTree(*tree.names)
    for val in combined_subclasses.values():
        result.add_subclass(val)
    return result

def build_type_table(tree):
    """
    Creates a dictionary where all the nodes of a tree
    are directly accessible by name.
    
    e.g.
       A
      / \
     B   C
          \
           D
    will become:
    {
        'A': (tree A containing B,C),
        'B': (tree B),
        'C': (tree C containing D),
        'D': (tree D)
    }
    """
    entries = {}
    for name in tree.names:
        entries[name] = tree
    for subclass in tree.subclasses:
        child_entries = build_type_table(subclass)
        for key, val in child_entries.items():
            if key in entries:
                throw_exception('CannotBuildTypeTable', 'Duplicate node name {0}'.format(key))
            else:
                entries[key] = val
    return entries

def get_type(value):
    kind = type(value)
    if kind is int:
        return 'Int'
    elif kind is float:
        return 'Double'
    elif kind is bool:
        return 'Boolean'
    elif kind is str:
        if value.startswith('#'):
            return 'Tag'
        else:
            return 'String'
    elif kind is list:
        return 'List'
    if value.__class__ is Ratio:
        return 'Ratio'
    elif value.__class__ is Table:
        return 'Table'
    elif value is None:
        return 'Null'
    elif kind is dict:
        # This is a user-defined object
        if '$type' in value:
            if value['$type'].startswith('"'):
                return value['$type'][1:-1]
            else:
                return value['$type']
        else:
            return 'Instance'
    elif str(value).startswith('<function'):
        return 'Function'
    elif value.__class__ is Trigger:
        return 'Trigger'
    throw_exception('UnknownType', str(value) + ' has an unknown type.')
    
def generate_default_tree():
    integers = TypeTree('Int', 'Integer')
    doubles = TypeTree('Double')
    bools = TypeTree('Boolean')
    strs = TypeTree('String')
    tags = TypeTree('Tag')
    lists = TypeTree('List')
    tables = TypeTree('Table')
    ratios = TypeTree('Ratio', 'Rational')
    nulls = TypeTree('Null', 'Void')
    functions = TypeTree('Function')
    instances = TypeTree('Instance')
    triggers = TypeTree('Trigger')
    
    numbers = TypeTree('Number')
    numbers.add_subclass(integers)
    numbers.add_subclass(doubles)
    numbers.add_subclass(ratios)
    
    sequences = TypeTree('Sequence', 'Iterable')
    sequences.add_subclass(strs)
    sequences.add_subclass(lists)
    sequences.add_subclass(tables)
    
    objects = TypeTree('Object')
    objects.add_subclass(numbers)
    objects.add_subclass(sequences)
    objects.add_subclass(tags)
    objects.add_subclass(bools)
    objects.add_subclass(nulls)
    objects.add_subclass(functions)
    objects.add_subclass(instances)
    objects.add_subclass(triggers)
    
    return build_type_table(objects)
