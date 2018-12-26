from control_flow import prepare_control_flow
from strtools import find_matching_quote
from exception import throw_exception

def is_quote(prgm, i):
    if i == 0:
        return prgm[0] == '"'
    else:
        return prgm[i] == '"' and prgm[i - 1] != '\\'

def convert_single_quotes(prgm):
    def escape_double_quotes(prgm):
        processed = ''
        for i in xrange(len(prgm)):
            if is_quote(prgm, i):
                processed += '\\"'
            else:
                processed += prgm[i]
        return processed
    processed = ''
    length = len(prgm)
    i = 0
    in_double_quotes = False
    while i < length:
        char = prgm[i]
        if is_quote(prgm, i):
            in_double_quotes = not in_double_quotes
        if char == "'" and not in_double_quotes:
            j = find_matching_quote(prgm[i + 1:], "'")
            if j == -1:
                throw_exception('NoClosingSingleQuote', 'No closing single quote in: ' + prgm)
            processed += '"' + escape_double_quotes(prgm[i+1 : i+j+1]) + '"'
            i += j + 1
        else:
            processed += char
        i += 1
    return processed

def preprocess(prgm):
    def remove_comments(prgm):
        """
        Removes single-line comments and multi-line comments,
        except those embedded in strings.
        """
        i = 0
        processed = ''
        length = len(prgm)
        in_quotes = False
        while i < length:
            char = prgm[i]
            if is_quote(prgm, i):
                in_quotes = not in_quotes
            if (not in_quotes) and char == '/' and i + 1 < length:
                next = prgm[i + 1]
                if next == '/':
                    # Scan forward until end of line
                    while i < length and prgm[i] != '\n':
                        i += 1
                    i -= 1
                elif next == '*':
                    # Scan forward until end of multi-line comment
                    while i < length and prgm[i : i+2] != '*/':
                        i += 1
                    i += 1
                else:
                    processed += char
            else:
                processed += char
            i += 1
        return processed
    def replace_special(prgm):
        i = 0
        processed = ''
        length = len(prgm)
        in_quotes = False
        while i < length:
            char = prgm[i]
            if is_quote(prgm, i):
                in_quotes = not in_quotes
            if in_quotes:
                if char == '(':
                    processed += '\\x28'
                elif char == ')':
                    processed += '\\x29'
                else:
                    processed += char
            else:
                processed += char
            i += 1
        return processed
    return replace_special(remove_comments(convert_single_quotes(prgm)))

def prepare_program(prgm):
    """
    Splits lines of a program and prepares control flow.
    """
    # TODO : handle semicolons embedded in string literals
    # and semicolons in the repl.
    prgm = preprocess(prgm)
    prgm = prgm.replace(';', '\n')
    lines = prgm.split('\n')
    lines = [line.strip() for line in lines]
    lines = prepare_control_flow(lines)
    return lines
