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
