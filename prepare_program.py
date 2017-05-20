from control_flow import prepare_control_flow

def prepare_program(prgm):
    """
    Splits lines of a program and prepares control flow.
    """
    lines = prgm.split('\n')
    lines = [line.strip() for line in lines]
    lines = prepare_control_flow(lines)
    return lines
