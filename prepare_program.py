from control_flow import prepare_control_flow
from exception import throw_exception

import re
import ast2
import operator_overload
import strtools
import line_manager
import execution

class BraceMatcher(object):
    # TODO : This class keeps a count of open braces
    #        for each type: '(', '[', '{'.
    #        Consider using a stack so that mismatched
    #        braces such as '[(])' are not considered valid.
    def __init__(self, is_repl):
        self.is_repl = is_repl
        self.reset()

    def reset(self):
        self.open_parens = 0
        self.open_brackets = 0
        self.open_braces = 0
        self.has_error = False

    def match_line(self, line):
        for i, char in enumerate(line):
            if char == '(':
                self.open_parens += 1
            elif char == '[':
                self.open_brackets += 1
            elif char == '{':
                self.open_braces += 1
            elif char == ')':
                self.open_parens -= 1
                if self.open_parens < 0:
                    self.found_unmatched('Parenthesis', i, line)
            elif char == ']':
                self.open_brackets -= 1
                if self.open_brackets < 0:
                    self.found_unmatched('Bracket', i, line)
            elif char == '}':
                self.open_braces -= 1
                if self.open_braces < 0:
                    self.found_unmatched('Brace', i, line)
            elif char == ',' and (not self.is_repl) and self.is_complete():
                return i  # found a comma not in any braces
        if self.is_repl:
            return self
        elif self.has_error:
            return i
        return -1  # no character index for unmatched brace

    def found_unmatched(self, brace_name, column, line):
        if self.is_repl:
            throw_exception('UnmatchedClose' + brace_name, 'At column {0} on line: {1}'.format(column, line))
        else:
            self.has_error = True

    def is_complete(self):
        return self.open_parens == 0 and self.open_brackets == 0 and \
               self.open_braces == 0

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
        if (not in_double_quotes) and prgm[i : i+2] in ('//', '/*'):
            if prgm[i + 1] == '/':
                # Scan until end of line
                while i < length and prgm[i] != '\n':
                    processed += prgm[i]
                    i += 1
                char = '\n'
            else:
                # Scan until end of comment
                while i < length and prgm[i : i+2] != '*/':
                    processed += prgm[i]
                    i += 1
                char = '*'
        elif is_quote(prgm, i):
            in_double_quotes = not in_double_quotes
        if char == "'" and not in_double_quotes:
            j = strtools.find_matching_quote(prgm[i + 1:], "'")
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
                processed += strtools.convert_special_char(char)
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

def find_op_keyword(line, op):
    """
    Finds the last operator or keyword in the line,
    returning the index at which it is located.
    Ignores any content in string literals.
    Return -1 if there is no such operator or keyword.
    """
    if op not in line:
        return -1
    in_double_quotes = False
    for i in reversed(xrange(len(line))):
        if is_quote(line, i):
            in_double_quotes = not in_double_quotes
        elif (not in_double_quotes) and line[i : i+len(op)] == op:
            return i
    return -1

def char_range(first, last):
    return ''.join(chr(n) for n in xrange(ord(first), ord(last) + 1))

ident_chars = '_$' + char_range('A', 'Z') + char_range('a', 'z') + char_range('0', '9')

def extract_lambda(line, brace_matcher):
    arrow_index = find_op_keyword(line, '->')
    if arrow_index == -1:
        return None
    # TODO : for pattern matching, allow nested braces such as [args]
    #        in an argument list
    begin_index = arrow_index - 1
    # Skip whitespace:
    while begin_index > 0 and line[begin_index] in ' \t':
        begin_index -= 1
    args = None
    if line[begin_index] == ')':
        begin_index -= 1
        while begin_index >= 0 and line[begin_index] != '(':
            begin_index -= 1
        args = line[begin_index : arrow_index].strip()
    else:
        while begin_index >= 1 and line[begin_index - 1] in ident_chars:
            begin_index -= 1
        args = '(' + line[begin_index : arrow_index].strip() + ')'
    arrow_index += 2  # move past the '->' token
    brace_matcher.reset()
    # Find the end of the lambda
    end_index = brace_matcher.match_line(line[arrow_index:])
    if end_index == -1:
        end_index = len(line)     # lambda stops at end of line
    else:
        end_index += arrow_index  # compensate for location of arrow
    body = line[arrow_index : end_index].strip()
    return args, body, begin_index, end_index

def get_nested_lambda(lambda_body):
    match_obj = re.match(r'\(*(\$lambda[0-9]+)\)*', lambda_body)
    if match_obj:
        return match_obj.group(1)
    return None

def scan_delim(line, i, accept, step):
    length = len(line)
    while i >= 0 and i < length:
        ch = line[i]
        if ch not in ' \t':
            return ch in accept
        i += step
    return False

def substr_at(line, i, substr):
    return line[i:].startswith(substr)

section_operators = [':', '^', '*', '/', '%', '+', '-', '==', '!=', '>=', '<=', '>', '<']
def lift_op_sections(line):
    in_double_quotes = False
    for i in xrange(len(line)):
        if is_quote(line, i):
            in_double_quotes = not in_double_quotes
        if in_double_quotes:
            continue
        for op in section_operators:
            if substr_at(line, i, op):
                right_start = i + len(op)
                if scan_delim(line, i - 1, ',([{', -1) and \
                   scan_delim(line, right_start, ',)]}', 1):
                    return line[:i] + '(a,b)->a{0}b'.format(op) + lift_op_sections(line[right_start:])
    return line

def interleave(lst, item):
    result = []
    for elem in lst:
        result.extend([elem, item])
    if len(result) >= 2:
        result.pop()
    return result

def decompose_function_calls(expr):
    tokens = ast2.AST(expr).parse()
    transformed = []
    for token in tokens:
        match_obj = re.match(r'(\$?[A-Za-z_][A-Za-z_0-9]*)\((.*)\)', token)
        if match_obj:
            func_name = match_obj.group(1)
            func_args = match_obj.group(2)
            arg_list = execution.split_args(func_args)
            transformed.extend([func_name, '('] + interleave(arg_list, ',') + [')'])
        else:
            transformed.append(token)
    return [token.strip() for token in transformed]

def extract_list_comprehension(line):
    has_state = False
    from_index = find_op_keyword(line, ' from ')
    if from_index == -1:
        return None
    begin_index = from_index - 1
    # Skip until pipe character
    while begin_index > 0 and line[begin_index] != '|':
        begin_index -= 1
    elem = line[begin_index + 1 : from_index].strip()
    pipe_index = begin_index
    while begin_index > 0 and line[begin_index] != '[':
        begin_index -= 1
    map_expr = line[begin_index + 1 : pipe_index].strip()
    map_tokens = decompose_function_calls(map_expr)
    if 'this' in map_tokens:
        map_expr = ''.join(('$stateList' if token == 'this' else token) for token in map_tokens)
        has_state = True
    right_start = from_index + len(' from ')
    end_index = right_start
    while end_index < len(line) and line[end_index] != ']':
        end_index += 1
    source = line[right_start : end_index].strip()
    return map_expr, elem, source, begin_index, end_index, has_state

def lift_list_comprehension(line):
    result = extract_list_comprehension(line)
    if result is None:
        return line
    map_expr, elem, source, begin_index, end_index, has_state = result
    if has_state:
        return lift_list_comprehension(line[:begin_index]) + \
               '$mapWithState(({0}, $stateList) -> {1}, {2})'.format(elem, map_expr, source) + \
               line[end_index + 1:]
    else:
        return lift_list_comprehension(line[:begin_index]) + \
               '$map({0} -> {1}, {2})'.format(elem, map_expr, source) + \
               line[end_index + 1:]

def split_statement(line):
    for keyword in special_statement_starters:
        if line.startswith(keyword):
            return keyword[:-1], line[len(keyword):]
    if line.startswith('func '):
        # TODO : allow default arguments in function definition
        split_index = line.find('=') + 1
        return line[:split_index], line[split_index:]
    op = extract_compound_operator_line(line, ast2.compound_operators)
    if op is not None:
        split_index = line.find(op) + 2
        return line[:split_index], line[split_index:]
    return '', line

def convert_ternary(line):
    # Scan the string first before doing extra work:
    if 'then' in line and 'else' in line:
        front, rest = split_statement(line)
        tokens = decompose_function_calls(rest)
        try:
            # TODO: this part needs to use BraceMatcher
            # and the BraceMatcher must be able to operate on lists
            delim_front = tokens.index('then')
            delim_rest = tokens.index('else')
        except ValueError:
            # It's possible that the tokens don't
            # form a real ternary, in which case
            # it's ok to continue:
            return line
        cond = ''.join(tokens[:delim_front])
        true_case = ''.join(tokens[delim_front + 1:delim_rest])
        false_case = ''.join(tokens[delim_rest + 1:])
        return front + ' $ternary({0}, {1}, {2})'.format(cond, true_case, false_case)
    return line

def lift_lambdas(line_mgr, env):
    line_mgr.for_each_line(lift_op_sections)
    brace_matcher = BraceMatcher(False)
    lambda_num = 0 if env is None else env.lambda_num
    new_line_mgr = line_manager.LineManager([])
    for i, line_data in line_mgr.enumerate_line_data():
        line = line_data.line
        lifted = []
        while True:
            line = lift_list_comprehension(convert_ternary(line))
            lambda_content = extract_lambda(line, brace_matcher)
            if lambda_content is None:
                break
            args, body, begin_index, end_index = lambda_content
            nested_lambda = get_nested_lambda(body)
            if nested_lambda is not None:
                if len(lifted) == 0:
                    throw_exception(
                        'InternalError',
                        'Lambda {0} was never defined'.format(nested_lambda)
                    )
                last_lambda_def = lifted.pop()
                # Warning: when generating these code lines, do not add
                # any indentation (leading whitespace) inside the string
                # literals. The code has already been preprocessed
                # to remove such whitespace.
                lifted.extend([
                    'sub $lambda{0}{1}'.format(lambda_num, args),
                    last_lambda_def,
                    'return ' + nested_lambda,
                    'end'
                ])
            else:
                lifted.append('func $lambda{0}{1} = {2}'.format(lambda_num, args, body))
            line = line[:begin_index] + '$lambda' + str(lambda_num) + line[end_index:]
            lambda_num += 1
        lifted.append(line)
        for ln in lifted:
            new_line_mgr.append_line_data(line_manager.LineData(ln, line_data.line_num, line_data.end_line_num))
    return new_line_mgr, lambda_num

def prepare_program(line_mgr):
    """
    Splits lines of a program and prepares control flow.
    """
    line_mgr.for_each_line(convert_compound_operator)
    line_mgr.for_each_line(convert_increment_decrement_operators)
    line_mgr.for_each_line(detect_and_replace_unary_minus)
    prepare_control_flow(line_mgr)
