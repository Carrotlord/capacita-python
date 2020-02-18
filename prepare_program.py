from control_flow import prepare_control_flow
from strtools import find_matching_quote, convert_special_char
from exception import throw_exception

import ast2
import operator_overload

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

def convert_compound_operator(line):
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
            return processed_line
    else:
        return line

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
    prgm = replace_special(remove_comments(convert_single_quotes(prgm)))
    # TODO : handle semicolons embedded in string literals
    # and semicolons in the repl.
    prgm = prgm.replace(';', '\n')
    return prgm

def convert_increment_decrement_operators(line):
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
    return line

special_statement_starters = [
    'print ', 'show ', 'return ',
    'if ', 'when ', 'while ', 'for ', 'repeat ', 'switch ',
    'else if ', 'case ', 'throw ', 'super '
]

# Any minus signs that follow one of these characters
# (ignoring any whitespace in the line)
# must be treated as an unary minus, not a binary minus.
significant_chars = '><=+-*/%~^:([{,|'

def replace_for_special_statements(line):
    for starter in special_statement_starters:
        if line.startswith(starter):
            without_starter = line[len(starter):]
            if without_starter.lstrip().startswith('-'):
                return line.replace('-', '~', 1)
    return line

def detect_and_replace_unary_minus(line):
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
    return processed_line

def is_op_overload_syntax(line):
    return line.startswith('sub ') and '(' not in line

ordered_overloadable_ops = [op for op in ast2.ordered_ops if ' ' not in op and op not in ['.', '~']]

def construct_equivalent_function_defn(line):
    if not is_op_overload_syntax(line):
        return line
    if line.endswith(' -this'):
        pieces = line.split()
        function_keyword = pieces[0]
        if len(pieces) == 2:
            return '{0} $negative()'.format(function_keyword)
        else:
            return_type = pieces[1]
            return '{0} {1} $negative()'.format(function_keyword, return_type)
    elif line.endswith(' not this'):
        pieces = line.split()
        function_keyword = pieces[0]
        if len(pieces) == 3:
            return '{0} $booleanNot()'.format(function_keyword)
        else:
            return_type = pieces[1]
            return '{0} {1} $booleanNot()'.format(function_keyword, return_type)
    else:
        found_operator = None
        for operator in ordered_overloadable_ops:
            if operator in line:
                # Only replace the first occurrence
                line = line.replace(operator, ' ', 1)
                found_operator = operator
                break
        if found_operator is not None:
            pieces = line.split()
            function_keyword = pieces[0]
            is_reflected = pieces[-1] == 'this'
            method_name = operator_overload.method_names[found_operator]
            if is_reflected:
                method_name = 'r' + method_name
                arg_name = pieces[-2]
            else:
                arg_name = pieces[-1]
            return_type = '' if len(pieces) == 3 else pieces[1] + ' '
            return '{0} {1}${2}({3})'.format(
                function_keyword,
                return_type,
                method_name,
                arg_name
            )
        else:
            throw_exception(
                'InvalidFunctionDefinition',
                "'{0}' is not a valid function definition".format(line)
            )

def find_assignment_operator(single_line_function):
    defn = single_line_function
    # 5 is the length of the string 'func '
    i = 5
    length = len(defn)
    while i + 1 < length:
        # Look for a standalone '=' operator, which should not be a part of
        # '==', '<=', '>=', or '!='
        if defn[i] == '=' and defn[i - 1] not in '<>=!' and defn[i + 1] != '=':
            return i
        i += 1
    throw_exception(
        'InvalidFunctionSyntax',
        'Single line function definition has no assignment operator:\n' + defn
    )

def replace_op_overload_syntax(line_mgr):
    i = 0
    while i < len(line_mgr):
        line = line_mgr[i]
        if line.startswith('func '):
            j = find_assignment_operator(line)
            defn = line[5:j]
            if '(' not in defn:
                return_expr = line[j + 1:]
                line_mgr[i : i+1] = [
                    'sub ' + defn.rstrip(),
                    'return ' + return_expr,
                    'end'
                ]
                i += 2
        i += 1
    line_mgr.for_each_line(construct_equivalent_function_defn)

def prepare_program(line_mgr):
    """
    Splits lines of a program and prepares control flow.
    """
    line_mgr.for_each_line(convert_compound_operator)
    line_mgr.for_each_line(convert_increment_decrement_operators)
    line_mgr.for_each_line(detect_and_replace_unary_minus)
    prepare_control_flow(line_mgr)
