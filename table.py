from exception import throw_exception

def hashable(value):
    dictionary = {}
    try:
        dictionary[value] = None
    except TypeError:
        return False
    return True

class Table(object):
    def __init__(self):
        self.hashable_pairs = {}
        self.unhashable_pairs = []
        self.ordered_keys = []
    
    def put(self, key, value):
        has_key = self.has_key(key)
        if not has_key:
            self.ordered_keys.append(key)
        if hashable(key):
            self.hashable_pairs[key] = value
        else:
            if has_key:
                self.modify_existing_unhashable(key, value)
            else:
                self.unhashable_pairs.append( (key, value) )
    
    def modify_existing_unhashable(self, key, value):
        for i in xrange(len(self.unhashable_pairs)):
            k, v = self.unhashable_pairs[i]
            if k == key:
                self.unhashable_pairs[i] = (key, value)
                return
        throw_exception('ModifyingKeyNotFound', 'Trying to modify key ' +
                        str(key) + ' that does not exist')
    
    def get(self, key):
        if hashable(key) and key in self.hashable_pairs:
            return self.hashable_pairs[key]
        else:
            for k, v in self.unhashable_pairs:
                if k == key:
                    return v
        throw_exception('KeyNotFound', 'Table has no key ' + str(key))
    
    def __getitem__(self, key):
        return self.get(key)
    
    def __setitem__(self, key, value):
        self.put(key, value)
        return self
    
    def __len__(self):
        return len(self.ordered_keys)
    
    def keys(self):
        return list(self.ordered_keys)
    
    def has_key(self, key):
        if hashable(key):
            return key in self.hashable_pairs
        return key in self.ordered_keys

    def __str__(self):
        return repr(self)
    
    def __repr__(self):
        representation = '{'
        i = 0
        for key in self.ordered_keys:
            representation += str(key) + ', ' + str(self.get(key))
            if i != len(self.ordered_keys) - 1:
                # This is not the final key
                representation += ' | '
            i += 1
        return representation + '}'
