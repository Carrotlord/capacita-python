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
    elif stmt.startswith('show '):
        return ['show', stmt[5:]]
    elif stmt.startswith(':cond '):
        return [':cond', stmt[6:]]
    elif stmt.startswith(':j '):
        return [':j', stmt[3:]]
    elif stmt.startswith(':jf '):
        return [':jf', stmt[4:]]
    elif stmt.startswith(':jt '):
        return [':jt', stmt[4:]]
    for i in range(len(stmt)):
        for op in operators:
            if stmt[i:i+len(op)] == op:
                return [
                    stmt[0:i].strip(),
                    op,
                    stmt[i+len(op):].strip()
                ]
    return []