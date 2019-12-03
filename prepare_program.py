from control_flow import prepare_control_flow
from strtools import find_matching_quote, convert_special_char
from exception import throw_exception

import ast2
import re
import operator_overload

def build_op_overload_regex(is_reflected):
    variable_regex = r'[A-Za-z_][A-Za-z_0-9]*'
    # ?? indicates an optional group which is non-greedy
    regex_start = r'(sub|func) ({0} )??'.format(variable_regex)
    op_group = r'('
    # re.escape(...) is necessary, since some operators are also regex metacharacters
    for operator in operator_overload.method_names:
        op_group += re.escape(operator) + '|'
    for unary_operator in operator_overload.unary_method_names:
        op_group += re.escape(unary_operator) + '|'
    # Remove last | character, and close the group with a closing parenthesis
    op_group = op_group[:-1] + r')'
    if is_reflected:
        # The following group is optional, to account for unary operators
        regex_middle = r'({0})?'.format(variable_regex)
        regex_end = r'\s*' + op_group + r'\s*this\s*'
    else:
        regex_middle = r'\s*this\s*' + op_group + r'\s*'
        # There are no postfix unary operators that can be overloaded, so this
        # group is not optional
        regex_end = r'({0})'.format(variable_regex)
    return regex_start + regex_middle + regex_end

op_overload_regex = build_op_overload_regex(False)
reflected_op_overload_regex = build_op_overload_regex(True)

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

special_statement_starters = [
    'print ', 'show ', 'return ',
    'if ', 'when ', 'while ', 'for ', 'repeat ', 'switch ',
    'else if ', 'case ', 'throw ', 'super '
]

# Any minus signs that follow one of these characters
# (ignoring any whitespace in the line)
# must be treated as an unary minus, not a binary minus.
significant_chars = '><=+-*/%~^:([{,|'

def detect_and_replace_unary_minus(lines):
    def replace_for_special_statements(line):
        for starter in special_statement_starters:
            if line.startswith(starter):
                without_starter = line[len(starter):]
                if without_starter.lstrip().startswith('-'):
                    return line.replace('-', '~', 1)
        return line
    processed_lines = []
    for line in lines:
        line = replace_for_special_statements(line)
        last_meaningful_char = None
        processed_line = ''
        for char in line:
            # Is this an unary minus sign? If so, replace with '~'.
            if char == '-' and last_meaningful_char is not None and \
               last_meaningful_char in significant_chars:
                char = '~'
            if not char.isspace():
                last_meaningful_char = char
            processed_line += char
        processed_lines.append(processed_line)
    return processed_lines

def construct_equivalent_function_defn(match_obj, is_reflected):
    function_keyword = match_obj.group(1)
    function_return_type = match_obj.group(2)
    if function_return_type is None:
        function_return_type = ''
    if is_reflected:
        arg_name = match_obj.group(3)
        operator_to_be_overloaded = match_obj.group(4)
    else:
        arg_name = match_obj.group(4)
        operator_to_be_overloaded = match_obj.group(3)
    if operator_to_be_overloaded in operator_overload.method_names:
        operator_method_name = operator_overload.method_names[operator_to_be_overloaded]
        is_unary = False
    elif operator_to_be_overloaded in operator_overload.unary_method_names:
        operator_method_name = operator_overload.unary_method_names[operator_to_be_overloaded]
        is_unary = True
    else:
        throw_exception(
            'UnknownOperator',
            '{0} is an operator that cannot be overloaded'.format(operator_to_be_overloaded)
        )
    if is_unary or arg_name is None:
        defn = '{0} {1}${2}()'.format(function_keyword, function_return_type, operator_method_name)
    else:
        defn = '{0} {1}${2}({3})'.format(function_keyword, function_return_type, operator_method_name, arg_name)
    return defn

def replace_op_overload_syntax(lines):
    # TODO : currently, this function is never called, except for test cases
    processed_lines = []
    for line in lines:
        match_obj = re.match(op_overload_regex, line)
        if match_obj:
            processed_lines.append(construct_equivalent_function_defn(match_obj, False))
        else:
            match_obj = re.match(reflected_op_overload_regex, line)
            if match_obj:
                processed_lines.append(construct_equivalent_function_defn(match_obj, True))
            else:
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
    lines = detect_and_replace_unary_minus(lines)
    lines = prepare_control_flow(lines)
    return lines
