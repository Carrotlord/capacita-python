from strtools import find_matching, find_matching_quote
from exception import throw_exception

import re

compound_operators = ['+=', '-=', '*=', '/=', '%=', '^=', ':=']

def is_numeric(val):
    """
    Returns True if val is an integer or float, else False.
    """
    try:
        int(val)
    except ValueError:
        try:
            float(val)
        except ValueError:
            return False
        else:
            return True
    else:
        return True

def is_positive_numeric(val):
    """
    Returns True if val is a positive integer or float, else False.
    """
    if not is_numeric(val):
        return False
    val = str(val)
    if len(val) > 0 and val[0] == '-':
        return False
    return True
    
def is_digit(val):
    return val in '0123456789'

def is_float_exponent_header(val):
    """
    Returns True if val begins a floating point literal with
    an exponent field, such as '3.0e' or '5e'.
    """
    if len(val) < 2:
        return False
    if val.startswith('-'):
        val = val[1:]
    return (val.endswith('e') or val.endswith('E')) and \
           is_digit(val[-2]) and is_digit(val[0])

class AST(object):
    """
    Abstract syntax tree with strongly binding operators at the bottom.
    The smaller the precedence, the stronger the binding.
    """
    def __init__(self, expr):
        """Setup expression and precedences of operators."""
        self.expr = expr
        self.precedences = {
            '.': 1,
            ':': 2,
            '^': 3,
            '*': 4, '/': 4, '%': 4,
            '+': 5, '-': 5,
            '==': 6, '!=': 6, '>=': 6, '<=': 6,
            '>': 6, '<': 6,
            ' of ': 7,
            'not ': 8,
            ' and ': 9, ' or ': 9, ' xor ': 9
        }
        # Longer operators should be detected before shorter ones:
        self.ordered_ops = [' and ', ' or ', ' xor ', 'not ', ' of ',
                            '>=', '<=', '!=', '==', '<', '>',
                            '+', '-', '*', '/', '%', '^', ':', '.']
        self.starters = ' n><!=+-*/%^:.'
    
    def weakest(self):
        """
        Returns the integer precedence of the most weakly binding
        operator in self.expr.
        """
        current = 0
        result = None
        for op in self.expr:
            if op in self.precedences and self.precedences[op] > current:
                current = self.precedences[op]
                result = op
        return result
        
    def split_list_elems(self):
        """
        Splits apart list and table literals into brackets, commas, and elements.
        e.g. '[1, 2+3, 4*5]' -> ['[', '1', ',', '2+3', ',', '4*5', ']']
        '{1, 2 | 3, 4}' -> ['{', '1', ',', '2', '|', '3', ',', '4', '}']
        """
        def append_if_not_empty(lst, elem):
            if len(elem) > 0:
                lst.append(elem)
        results = []
        buffer = ''
        delimiters = ['[', ']', ',', '{', '}', '|']
        i = 0
        while i < len(self.expr):
            char = self.expr[i]
            if char in delimiters:
                append_if_not_empty(results, buffer)
                results.append(char)
                buffer = ''
            elif char == '(':
                j = find_matching(self.expr[i + 1:])
                if j == -1:
                    throw_exception('UnmatchedOpeningParenthesis', self.expr)
                buffer += self.expr[i : i+j]
                i += j
                continue
            elif char == '"':
                j = find_matching_quote(self.expr[i + 1:])
                if j == -1:
                    throw_exception('UnmatchedQuote', self.expr)
                buffer += self.expr[i : i+j+1] + '"'
                i += j + 1
            else:
                buffer += char
            i += 1
        append_if_not_empty(results, buffer)
        return results
        
    def parse(self):
        results = []
        elems = self.split_list_elems()
        for elem in elems:
            results += self.parse_elem(elem)
        return results
        
    def parse_elem(self, expr):
        """
        Splits an expression based on its operators.
        e.g. '2 + 3*4' -> ['2', '+', '3', '*', '4']
        """
        buffer = ''
        tokens = []
        expr_length = len(expr)
        i = 0
        in_quotes = False
        while i < expr_length:
            next_char = expr[i]
            if next_char == '(':
                paren_close = find_matching(expr[i + 1:])
                if paren_close == -1:
                    throw_exception('UnmatchedOpeningParenthesis', expr)
                buffer += '(' + expr[i+1 : i+paren_close]
                i += paren_close
            else:
                op_detected = False
                if (not in_quotes) and next_char in self.starters:
                    for op in self.ordered_ops:
                        op_length = len(op)
                        if expr[i : i+op_length] == op and \
                           not(op == '.' and is_digit(expr[i+1 : i+2])):
                            buffer_contents = buffer.strip()
                            if len(buffer_contents) > 0:
                                tokens.append(buffer_contents)
                            tokens.append(op)
                            buffer = ''
                            i += op_length
                            op_detected = True
                            break
                if not op_detected:
                    if next_char == '"':
                        in_quotes = not in_quotes
                    buffer += next_char
                    i += 1
        buffer_contents = buffer.strip()
        if len(buffer_contents) > 0:
            tokens.append(buffer_contents)
        return self.merge_exponent_notation(self.merge_negatives(tokens))
    
    def merge_negatives(self, tokens):
        """
        Allows for proper expression of the unary operator '-'
        e.g. ['-', '233', '+', '-', '18', ':', '-', '1']
             -> ['-233', '+', '-18', ':', '-1']
        """
        if len(tokens) <= 1:
            return tokens
        if tokens[0] == '-' and is_positive_numeric(tokens[1]):
            return self.merge_negatives(['-' + str(tokens[1])] + tokens[2:])
        i = 0
        max_len = len(tokens) - 2
        while i < max_len:
            if tokens[i] in self.precedences and tokens[i + 1] == '-' and \
               is_positive_numeric(tokens[i + 2]):
                tokens[i+1 : i+3] = ['-' + str(tokens[i + 2])]
                max_len = len(tokens) - 2
            i += 1
        return tokens

    def merge_exponent_notation(self, tokens):
        """
        Allows for proper expression of float literals
        with exponent fields, such as 3e-20.
        e.g. ['-3.0e5', '+', '186e', '-', '20', '*', '1e', '-', '6']
             -> ['-3.0e5', '+', '186e-20', '*', '1e-6']
        """
        i = 0
        while i < len(tokens):
            current_token = tokens[i]
            if is_float_exponent_header(current_token):
                # Combine the next one or two tokens with the current one
                num_tokens = None
                if tokens[i + 1] in ['+', '-']:
                    num_tokens = 3
                else:
                    num_tokens = 2
                tokens[i : i+num_tokens] = [''.join(tokens[i : i+num_tokens])]
            i += 1
        return tokens

    def build_indices(self):
        """
        Takes a list of tokens and collects indices of operators
        based on their precedence. The first index encountered indicates
        which operators should be evaluated first.
        e.g. '1+1+3*4^7' -> ['1', '+', '1', '+', '3', '*', '4', '^', '7']
                   indices:   0    1    2    3    4    5    6    7    8
             -> [[], [7], [5], [1, 3]]
        """
        tokens = self.parse()
        table = [[], [], [], [], [], [], [], [], []]
        i = 0
        for token in tokens:
            if token in self.precedences:
                if token == 'not ':
                    table[self.precedences[token] - 1].append((i,))
                else:
                    table[self.precedences[token] - 1].append(i)
            i += 1
        return table
    
    def reduce_index(self, all, j, amount):
        if type(all[j]) is tuple:
            all[j] = (all[j][0] - amount,)
        else:
            all[j] -= amount
    
    def collapse_indices(self, index_table):
        """
        Given a table of indices, determines which 'final' index
        the operators will be at during each stage of simplification.
        e.g. [[], [7], [5], [1, 3]]
          -> [7, 5, 1, 3]
          -> [7, 5, 1, 1]
        Notice the last index was shifted to the left by 2 thanks
        to the simplification that occurred previously.
        """
        all = []
        for index_list in index_table:
            all += index_list
        i = 0
        for index in all:
            j = i + 1
            for checked_index in all[i+1:]:
                is_unary = type(index) is tuple
                # Pull values out of tuples so they can be compared properly.
                if is_unary:
                    raw_index = index[0]
                else:
                    raw_index = index
                if type(checked_index) is tuple:
                    raw_checked_index = checked_index[0]
                else:
                    raw_checked_index = checked_index
                # When the current raw_index is processed via operator
                # evaluation, it will reduce the length of the token list
                # by 2 (or by 1, if the opeator is unary).
                # In this case, all indices greater than raw_index
                # must be reduced by either 2 or 1.
                if raw_index < raw_checked_index:
                    if is_unary:
                        self.reduce_index(all, j, 1)
                    else:
                        self.reduce_index(all, j, 2)
                j += 1
            i += 1
        for i in xrange(len(all)):
            if type(all[i]) is tuple:
                all[i] = all[i][0]
        return all
