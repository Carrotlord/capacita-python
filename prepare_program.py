from control_flow import prepare_control_flow

def prepare_program(prgm):
    lines = prgm.split('\n')
    lines = [line.strip() for line in lines]
    lines = prepare_control_flow(lines)
    return lines
