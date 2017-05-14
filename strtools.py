def find_matching(expr):
    """
    Finds the first unmatched closing parenthesis
    returns -1 when there is no matching parenthesis.
    """
    num_open = 0
    i = 0
    for char in expr:
        if char == '(':
            num_open += 1
        elif char == ')':
            if num_open == 0:
                return i + 1
            else:
                num_open -= 1
        i += 1
    return -1
