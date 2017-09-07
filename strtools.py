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

def find_matching_quote(expr):
    """
    Finds the next double-quote in expr.
    """
    # TODO : allow for escaped quotes
    return expr.find('"')
