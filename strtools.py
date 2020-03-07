import exception

def concat_cap_strings(a, b):
    return CapString(a.contents + b.contents, False)

class CapString(object):
    def __init__(self, contents, should_escape=True):
        if should_escape:
            self.contents = escape(contents)
        else:
            self.contents = contents

    def __add__(self, other):
        if other.__class__ is CapString:
            return concat_cap_strings(self, other)
        return CapString(self.contents + str(other), False)

    def __radd__(self, other):
        if other.__class__ is CapString:
            return concat_cap_strings(other, self)
        return CapString(str(other) + self.contents, False)

    def __float__(self):
        return float(self.contents)

    def __str__(self):
        return '"' + self.contents + '"'

    def __repr__(self):
        return repr(str(self))

    def __eq__(self, other):
        if other.__class__ is not CapString:
            return False
        return self.contents == other.contents

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.contents)

    def __len__(self):
        return len(self.contents)

    def __getitem__(self, index):
        return self.contents[index]

def find_matching(expr, opening='(', closing=')'):
    """
    Finds the first unmatched closing parenthesis
    returns -1 when there is no matching parenthesis.
    
    'opening' and 'closing' can be replaced with
    square brackets, curly brackets, or similar
    delimiters.
    """
    num_open = 0
    i = 0
    for char in expr:
        if char == opening:
            num_open += 1
        elif char == closing:
            if num_open == 0:
                return i + 1
            else:
                num_open -= 1
        i += 1
    return -1

def find_matching_quote(expr, quote='"'):
    """
    Finds the next double-quote in expr.
    """
    for i in xrange(len(expr)):
        if expr[i] == quote:
            if i == 0:
                return 0
            elif expr[i - 1] != '\\':
                return i
    return -1

def escape(str_contents):
    processed = ''
    i = 0
    length = len(str_contents)
    while i < length:
        if i + 1 < length and str_contents[i] == '\\':
            next = str_contents[i + 1]
            # TODO : more escape sequences exist, which need to be
            # accounted for.
            if next == '\\':
                processed += '\\'
            elif next == 'n':
                processed += '\n'
            elif next == 't':
                processed += '\t'
            elif next == 'q':
                processed += '"'
            elif next == 'x':
                # Hexadecimal character code
                processed += chr(int(str_contents[i+2 : i+4], 16))
                i += 2
            else:
                # Unrecognized escape sequence. Default to the literal character:
                processed += next
            i += 1
        else:
            processed += str_contents[i]
        i += 1
    return processed

def unescape(str_contents):
    replacements = {
        '\\': '\\\\',
        '\n': '\\n',
        '\t': '\\t',
        '"': '\\"'
    }
    processed = ''
    for char in str_contents:
        if char in replacements:
            processed += replacements[char]
        else:
            processed += char
    return processed

def convert_special_char(char):
    if char == '(':
        return '\\x28'
    elif char == ')':
        return '\\x29'
    else:
        return char

def validate_string_index(string, i):
    length = len(string)
    # Indices can be negative, with -1 signifying the last char
    if i < -length or i >= length:
        exception.throw_exception(
             'StringIndexOutOfBounds',
             'Index {0} is out of bounds for {1}'.format(i, string)
        )

def index_string(obj, i):
    validate_string_index(obj, i)
    char = obj[i]
    return CapString(char, False)
