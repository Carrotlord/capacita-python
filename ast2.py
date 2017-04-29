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

class AST(object):
    """
    Abstract syntax tree with strongly binding operators at the bottom.
    The smaller the precedence, the stronger the binding.
    """
    def __init__(self, expr):
        """Setup expression and precedences of operators."""
        self.expr = expr
        self.precedences = {
            ':': 1,
            '^': 2,
            '*': 3, '/': 3,
            '+': 4, '-': 4,
            '==': 5, '!=': 5, '>=': 5, '<=': 5,
            '>': 5, '<': 5,
            ' and ': 6, ' or ': 6, ' xor ': 6
        }
        # Longer operators should be detected before shorter ones:
        self.ordered_ops = [' and ', ' or ', ' xor ',
                            '>=', '<=', '!=', '==', '<', '>',
                            '+', '-', '*', '/', '^', ':']
    
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
        
    def parse(self):
        """
        Splits an expression based on its operators.
        e.g. '2 + 3*4' -> ['2', '+', '3', '*', '4']
        """
        buffer = ''
        tokens = []
        expr_length = len(self.expr)
        i = 0
        while i < expr_length:
            op_detected = False
            for op in self.ordered_ops:
                op_length = len(op)
                if self.expr[i : i+op_length] == op:
                    buffer_contents = buffer.strip()
                    if len(buffer_contents) > 0:
                        tokens.append(buffer_contents)
                    tokens.append(op)
                    buffer = ''
                    i += op_length
                    op_detected = True
                    break
            if not op_detected:
                buffer += self.expr[i]
                i += 1
        buffer_contents = buffer.strip()
        if len(buffer_contents) > 0:
            tokens.append(buffer_contents)
        return self.merge_negatives(tokens)
    
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
        table = [[], [], [], [], [], []]
        i = 0
        for token in tokens:
            if token in self.precedences:
                table[self.precedences[token] - 1].append(i)
            i += 1
        return table
    
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
                # Indices that are greater than
                # the current should be moved over 2 slots:
                if index < checked_index:
                    all[j] -= 2
                j += 1
            i += 1
        return all