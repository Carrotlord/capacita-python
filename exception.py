def throw_exception(kind, msg):
    """
    Throws a Capacita exception and exits the program.
    """
    print(kind + ' exception')
    print(msg)
    exit()

def throw_exception_with_line(kind, msg, line_mgr, prgm_counter):
    print('Error: ' + kind + ' exception')
    print(msg)
    if line_mgr is None or prgm_counter >= len(line_mgr):
        exit()
    line_data = line_mgr.get_line_data(prgm_counter)
    print('Original source code:')
    # First line is considered 'line 1', not 'line 0'
    if line_data.line_num == line_data.end_line_num:
        print('    Line {0}: {1}'.format(line_data.line_num + 1, line_mgr[prgm_counter]))
    else:
        print('    Line {0}-{1}: {2}'.format(
            line_data.line_num + 1,
            line_data.end_line_num + 1,
            line_mgr[prgm_counter]
        ))
    print('Internal code:')
    low = prgm_counter - 3
    high = prgm_counter + 3
    if low < 0:
        low = 0
    if high >= len(line_mgr):
        high = len(line_mgr) - 1
    for i in xrange(low, high + 1):
        if len(line_mgr[i]) == 0:
            line = ':no_operation'
        else:
            line = line_mgr[i]
        if i == prgm_counter:
            print('--> Line {0}: {1}'.format(i + 1, line))
        else:
            print('    Line {0}: {1}'.format(i + 1, line))
    exit()
