from exception import throw_exception

def find_next_end_else(lines, start, end_only=False):
    """
    Returns the corresponding end-statement or else-statement
    for the given clause-opener (which can be an if-statement,
    while-statement, etc.)
    Skips over end and else statements that are part of nested clauses.
    If end_only is set to True, all else statements are passed over.
    """
    i = start
    open_clauses = 0
    openers = ['if ', 'while ', 'for ', 'repeat ', 'switch ', 'sub ']
    while i < len(lines):
        line = lines[i]
        if line == 'end':
            if open_clauses == 0:
                return ['end', i]
            else:
                open_clauses -= 1
        elif (not end_only) and line == 'else' and open_clauses == 0:
            return ['else', i]
        else:
            for opener in openers:
                if line.startswith(opener):
                    open_clauses += 1
                    break
        i += 1
    throw_exception('NoEndStatement', 'Corresponding end statement does not exist.')

def prepare_control_flow(lines):
    """
    Converts if-statements, while-statements, for-statements, etc.
    into :cond and jump directives
    (:j for unconditional jump,
     :jt for jump true, and :jf for jump false).

    e.g.
    x = 100
    if x > 0
        // do something
    else
        // do other thing
    end

    0: x = 100
    1: :cond x > 0
    2: :jf 5
    3: // do something
    4: :j 6
    5: // do other thing
    6: 
    """
    def replace_labels(lines):
        """
        Replaces labels in jump directives with the actual
        addresses being jumped to.
        """
        label_table = {}
        i = 0
        for line in lines:
            if line.startswith(':label'):
                label_table[line[6:]] = i
                # Erase the label at this line:
                lines[i] = ''
            i += 1
        i = 0
        jumps = [':j ', ':jt ', ':jf ']
        for line in lines:
            for jump in jumps:
                if line.startswith(jump + 'label'):
                    label_num = line[len(jump) + 5:]
                    if label_num in label_table:
                        lines[i] = jump + str(label_table[label_num])
                        break
            i += 1
        return lines
    def prepare_else_ifs(lines):
        """
        Splits else-if statements into two separate lines:
        else followed by an if.
        Adds additional end statements for padding.
        This allows else-if statements to be evaluated using
        only basic if-else logic. For example, the following
        structures are equivalent:
        
        x = 2
        if x == 1
            A
        else if x == 2
            B
        else
            C
        end
        
        x = 2
        if x == 1
            A
        else
            if x == 2
                B
            else
                C
            end
        end
        """
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith('if '):
                # Find the end statement:
                _, end = find_next_end_else(lines, i + 1, True)
                j = i + 1
                # Keep track of how many else-ifs were split:
                splits = 0
                while j < end:
                    other_line = lines[j]
                    if other_line.startswith('else if '):
                        lines[j : j+1] = ['else', other_line[5:]]
                        end += 1
                        splits += 1
                    j += 1
                # Add extra end statements:
                lines[end : end+1] = ['end' for _ in xrange(splits + 1)]
            i += 1
        return lines
    def prepare_breaks_continues(lines):
        """
        Replace 'break' with 'break 1' and 'continue' with
        'continue 1'.
        Thus, all breaks and continues will be supplied
        with a depth parameter.
        """
        i = 0
        while i < len(lines):
            line = lines[i]
            if line == 'break':
                lines[i] = 'break 1'
            elif line == 'continue':
                lines[i] = 'continue 1'
            i += 1
        return lines
    def replace_for(lines):
        """
        Replaces for loops with while loops.
        
        for i = 0; i < 10; i++
            print i
        end
        
        i = 0
        while i < 10
            print i
            i++
        end
        """
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith('for '):
                initialization = line[4:]
                condition = lines[i + 1]
                increment = lines[i + 2]
                _, j = find_next_end_else(lines, i + 1, True)
                lines[j : j+1] = [increment, 'end']
                lines[i : i+3] = [initialization, 'while ' + condition]
            i += 1
        return lines
    def replace_for_each(lines):
        """
        Replaces for-each loops with for loops.
        
        for each x of xs
            print x
        end
        
        for $v0 = 0; $v0 < xs.length(); $v0++
            x = xs[$v0]
            print x
        end
        """
        # TODO : finish this function
        pass
    lines = prepare_else_ifs(lines)
    lines = prepare_breaks_continues(lines)
    lines = replace_for(lines)
    i = 0
    label_counter = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('when '):
            lines[i : i+1] = [':cond ' + line[5:], ':jf ' + str(i + 3)]
        elif line.startswith('if '):
            lines[i : i+1] = [':cond ' + line[3:], ':jf label' + str(label_counter)]
            # Find the next else or end statement:
            kind, j = find_next_end_else(lines, i + 2)
            if kind == 'end':
                lines[j] = ':label' + str(label_counter)
            else:
                # kind must be an else statement.
                # replace the else statement with a jump:
                else_label = ':label' + str(label_counter)
                label_counter += 1
                lines[j : j+1] = [':j label' + str(label_counter), else_label]
                kind, end = find_next_end_else(lines, j + 1)
                if kind == 'else':
                    throw_exception('MultipleElseStatement',
                                    'if statements cannot have multiple else clauses'
                                    ' (aside from else-if statements).')
                lines[end] = ':label' + str(label_counter)
            label_counter += 1
        elif line.startswith('while '):
            # label_leave is used to exit the loop:
            label_leave = str(label_counter)
            label_counter += 1
            # label_loop is used to repeat the loop:
            label_loop = str(label_counter)
            label_counter += 1
            lines[i : i+1] = [':cond ' + line[6:], ':jf label' + label_leave, ':label' + label_loop]
            kind, j = find_next_end_else(lines, i + 3)
            if kind == 'end':
                lines[j : j+1] = [':cond ' + line[6:], ':jt label' + label_loop, ':label' + label_leave]
                k = i + 3
                depth = 1
                # stack for keeping track of end statements:
                stack = []
                # Handle 'continue' and 'break' statements:
                while k < j:
                    current = lines[k]
                    if current.startswith('while '):
                        _, end = find_next_end_else(lines, k + 1, True)
                        depth += 1
                        stack.append(end)
                    elif len(stack) > 0 and current == 'end' and stack[-1] == k:
                        # This is the end to a nested while loop:
                        stack.pop()
                        depth -= 1
                    elif current == 'break ' + str(depth):
                        lines[k] = ':j label' + label_leave
                    elif current == 'continue ' + str(depth):
                        lines[k] = ':j label' + label_loop
                    k += 1
            else:
                throw_exception('InvalidElseStatement',
                                'While loops cannot have else statements.')
        i += 1
    lines = replace_labels(lines)
    return lines
