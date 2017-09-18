from control_flow import prepare_control_flow

def prepare_program(prgm):
    """
    Splits lines of a program and prepares control flow.
    """
    # TODO : handle semicolons embedded in string literals
    # and semicolons in the repl.
    prgm = prgm.replace(';', '\n')
    lines = prgm.split('\n')
    lines = [line.strip() for line in lines]
    lines = prepare_control_flow(lines)
    return lines
