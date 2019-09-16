from control_flow import prepare_control_flow
from strtools import find_matching_quote, convert_special_char
from exception import throw_exception

import ast2

def is_quote(prgm, i):
    if i == 0:
        return prgm[0] == '"'
    else:
        return prgm[i] == '"' and prgm[i - 1] != '\\'

def remove_quoted_strings(line):
    processed = ''
    i = 0
    in_double_quotes = False
    while i < len(line):
        if is_quote(line, i):
            in_double_quotes = not in_double_quotes
        elif not in_double_quotes:
            processed += line[i]
        i += 1
    return processed

def extract_compound_operator_line(line, operators):
    line_without_strings = remove_quoted_strings(line)
    for operator in operators:
        if operator in line_without_strings:
            return operator
    return None

def convert_compound_operators(prgm):
    lines = prgm.split('\n')
    processed_lines = []
    for line in lines:
        operator = extract_compound_operator_line(line, ast2.compound_operators)
        if operator is not None:
            # All compound operators take the form of '$=',
            # where 'a $= b' expands to 'a = a $ b'
            actual_operator = operator[0]
            pieces = line.split(operator)
            variable = (pieces[0]).strip()
            right_hand_side = pieces[1]
            if ' ' in variable:
                throw_exception(
                    'DeclaredTypeCompoundOperator',
                    'Can only use compound operator {0} when variable already ' \
                    'exists (cannot declare type of variable in this case)'.format(operator)
                )
            else:
                # Expand 'a $= b' into 'a=a$ (b)'
                # For instance, 'x *= y + z' becomes 'x=x*( y + z)'
                processed_line = '{0}={0}{1}({2})'.format(variable, actual_operator, right_hand_side)
                processed_lines.append(processed_line)
        else:
            processed_lines.append(line)
    return '\n'.join(processed_lines)

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
                processed += convert_special_char(char)
            else:
                processed += char
            i += 1
        return processed
    return replace_special(remove_comments(convert_single_quotes(prgm)))

def convert_increment_decrement_operators(lines):
    processed_lines = []
    for line in lines:
        if line.startswith('++') or line.startswith('--'):
            # Change prefix notation to postfix notation
            line = line[2:] + line[:2]
        if line.endswith('++'):
            operation = '+'
        elif line.endswith('--'):
            operation = '-'
        else:
            operation = None
        if operation is not None:
            if '.' in line or '[' in line:
                # This is a complex statement, which includes
                # a dot operator or index assignment.
                reference = line[:-2]
                line = '{0}={0}{1}1'.format(reference, operation)
            else:
                # This is a simple statement, for an ordinary
                # variable name.
                var_name = line[:-2]
                if operation == '+':
                    directive_name = 'inc'
                else:
                    directive_name = 'dec'
                line = ':{0} {1}'.format(directive_name, var_name)
        processed_lines.append(line)
    return processed_lines

def prepare_program(prgm):
    """
    Splits lines of a program and prepares control flow.
    """
    # TODO : handle semicolons embedded in string literals
    # and semicolons in the repl.
    prgm = preprocess(prgm)
    prgm = prgm.replace(';', '\n')
    prgm = convert_compound_operators(prgm)
    lines = prgm.split('\n')
    lines = [line.strip() for line in lines]
    lines = convert_increment_decrement_operators(lines)
    lines = prepare_control_flow(lines)
    return lines
