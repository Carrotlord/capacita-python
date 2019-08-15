operators = ['+=', '=']

# TODO: finish this function
def tokenize_statement(stmt):
    """
    Tokenizes a statement based on keywords and assignment operators.
    e.g. 'print 2+2' -> ['print', '2+2']
         'x += 5 * 6'    -> ['x', '+=', '5 * 6']
    """
    if stmt.startswith('print '):
        return ['print', stmt[6:]]
    elif stmt.startswith('import '):
        return ['import', stmt[7:]]
    elif stmt.startswith('super '):
        return ['super', stmt[6:]]
    elif stmt.startswith('func '):
        return ['func', stmt[5:]]
    elif stmt.startswith('show '):
        return ['show', stmt[5:]]
    elif stmt.startswith('return '):
        return ['return', stmt[7:]]
    elif stmt.startswith(':cond '):
        return [':cond', stmt[6:]]
    elif stmt.startswith(':j '):
        return [':j', stmt[3:]]
    elif stmt.startswith(':jf '):
        return [':jf', stmt[4:]]
    elif stmt.startswith(':jt '):
        return [':jt', stmt[4:]]
    elif stmt.startswith(':hook '):
        return [':hook', stmt[6:]]
    elif stmt == ':skiptoelse':
        return [':skiptoelse']
    elif stmt == 'try':
        return ['try']
    elif stmt == 'end':
        return ['end']
    elif stmt == 'else':
        return ['else']
    elif stmt.startswith('catch'):
        return ['catch', stmt[6:]]
    elif stmt.startswith('throw'):
        return ['throw', stmt[6:]]
    for i in range(len(stmt)):
        for op in operators:
            if stmt[i:i+len(op)] == op:
                return [
                    stmt[0:i].strip(),
                    op,
                    stmt[i+len(op):].strip()
                ]
    return []

def seek_parenthesis_in_tokens(tokens):
    """
    Locates a parenthesis in a token list.
    The return value is the index of the token element.
    
    e.g. ['x', '*', '(y+3)'] -> 2
    
    Returns None if there is no parenthesis in any of the tokens.
    Because of the way that ast.parse_elem(...) works, a token containing
    a pair of parentheses must always start and end with a parenthesis.
    """
    for i, token in enumerate(tokens):
        if type(token) is str and token.startswith('('):
            return i
    return None
