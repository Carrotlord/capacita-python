from control_flow import prepare_control_flow

def is_quote(prgm, i):
    if i == 0:
        return prgm[0] == '"'
    else:
        return prgm[i] == '"' and prgm[i - 1] != '\\'

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
    return replace_special(remove_comments(prgm))

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
