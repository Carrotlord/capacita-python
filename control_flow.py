from exception import throw_exception

import re

openers = ['if ', 'while ', 'for ', 'repeat ', 'switch ', 'sub ', ':for ']

def find_next_end_else(line_mgr, start, end_only=False, allow_catch=False):
    """
    Returns the corresponding end-statement or else-statement
    or catch-statement
    for the given clause-opener (which can be an if-statement,
    while-statement, etc.)
    Skips over end and else statements that are part of nested clauses.
    If end_only is set to True, all else statements are passed over.
    """
    i = start
    open_clauses = 0
    while i < len(line_mgr):
        line = line_mgr[i]
        if line == 'end':
            if open_clauses == 0:
                return ['end', i]
            else:
                open_clauses -= 1
        elif (not end_only) and line == 'else' and open_clauses == 0:
            return ['else', i]
        elif (not end_only) and allow_catch and \
             line.startswith('catch ') and open_clauses == 0:
            return ['catch', i]
        else:
            for opener in openers:
                if line.startswith(opener) or line == 'try':
                    open_clauses += 1
                    break
        i += 1
    throw_exception('NoEndStatement', 'Corresponding end statement does not exist.')

def is_loop(line):
    return line.startswith('while ') or line.startswith(':for ')

def prepare_control_flow(line_mgr):
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
    def replace_labels(line_mgr):
        """
        Replaces labels in jump directives with the actual
        addresses being jumped to.
        """
        label_table = {}
        i = 0
        for line in line_mgr.get_lines():
            if line.startswith(':label'):
                label_table[line[6:]] = i
                # Erase the label at this line:
                line_mgr[i] = ''
            i += 1
        i = 0
        jumps = [':j ', ':jt ', ':jf ']
        for line in line_mgr.get_lines():
            for jump in jumps:
                if line.startswith(jump + 'label'):
                    label_num = line[len(jump) + 5:]
                    if label_num in label_table:
                        line_mgr[i] = jump + str(label_table[label_num])
                        break
            i += 1
    def prepare_else_ifs(line_mgr):
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
        while i < len(line_mgr):
            line = line_mgr[i]
            if line.startswith('if '):
                # Find the end statement:
                _, end = find_next_end_else(line_mgr, i + 1, True)
                j = i + 1
                # Keep track of how many else-ifs were split:
                splits = 0
                while j < end:
                    other_line = line_mgr[j]
                    if other_line.startswith('else if '):
                        line_mgr[j : j+1] = ['else', other_line[5:]]
                        end += 1
                        splits += 1
                    j += 1
                # Add extra end statements:
                line_mgr[end : end+1] = ['end' for _ in xrange(splits + 1)]
            i += 1
    def prepare_breaks_continues(line):
        """
        Replace 'break' with 'break 1' and 'continue' with
        'continue 1'.
        Thus, all breaks and continues will be supplied
        with a depth parameter.
        """
        if line == 'break':
            return 'break 1'
        elif line == 'continue':
            return 'continue 1'
        else:
            return line
    def replace_for(line_mgr):
        """
        Replaces for loops with for directives,
        eventually translated to the equivalent of a while loop.
        
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
        while i < len(line_mgr):
            line = line_mgr[i]
            if line.startswith('for '):
                initialization = line[4:]
                condition = line_mgr[i + 1]
                increment = line_mgr[i + 2]
                _, j = find_next_end_else(line_mgr, i + 1, True)
                line_mgr[j : j+1] = [increment, 'end']
                line_mgr[i : i+3] = [initialization, ':for ' + condition, increment]
            i += 1
    def replace_for_each(line_mgr):
        """
        Replaces for-each loops with while loops.
        
        for each x of xs
            print x
        end
        
        $v0 = 0
        while $v0 < xs.length()
            x = xs[$v0]
            print x
            $v0++
        end
        """
        i = 0
        index_var_num = 0
        while i < len(line_mgr):
            line = line_mgr[i]
            match_obj = re.match(r'for each ([A-Za-z_][A-Za-z_0-9]*) of (.*)', line)
            if match_obj:
                elem_var = match_obj.group(1)
                iterable = match_obj.group(2)
                index_var = '$i' + str(index_var_num)
                initialization = index_var + '=0'
                condition = index_var + '<' + iterable + '.length()'
                increment = index_var + '+=1'
                assignment = elem_var + '=' + iterable + '[' + index_var + ']'
                _, j = find_next_end_else(line_mgr, i + 1, True)
                line_mgr[j : j+1] = [increment, 'end']
                # Temporarily place the increment statement after the :for directive,
                # so it can be used when processing continue statements.
                line_mgr[i : i+1] = [initialization, ':for ' + condition, increment, assignment]
                index_var_num += 1
            i += 1
    def insert_skips(line_mgr):
        """
        Insert :skiptoelse statements into try-catch blocks
        """
        i = 0
        while i < len(line_mgr):
            line = line_mgr[i]
            if line == 'try':
                kind, j = find_next_end_else(line_mgr, i + 1, False, True)
                if kind != 'catch':
                    throw_exception('CannotFindCatch', 'Line found that was not catch statement: ' + str(line_mgr[j]))
                catch_statement = line_mgr[j]
                line_mgr[j : j+1] = [':skiptoelse', catch_statement]
            i += 1
    def replace_when_continue(line_mgr):
        """
        Transforms a when statement containing a continue in its clause
        into an if statement.

        when CONDITION
            continue 2

        if CONDITION
            continue 2
        end

        This is so that continue statements can be replaced by an
        increment statement followed by a continue, which is needed
        in for loops and for-each loops.
        """
        i = 0
        while i + 1 < len(line_mgr):
            current_line = line_mgr[i]
            next_line = line_mgr[i + 1]
            if current_line.startswith('when ') and next_line.startswith('continue '):
                line_mgr[i : i+2] = [
                    'if ' + current_line[5:],
                    next_line,
                    'end'
                ]
            i += 1
    prepare_else_ifs(line_mgr)
    line_mgr.for_each_line(prepare_breaks_continues)
    replace_when_continue(line_mgr)
    replace_for_each(line_mgr)
    replace_for(line_mgr)
    insert_skips(line_mgr)
    i = 0
    label_counter = 0
    while i < len(line_mgr):
        line = line_mgr[i]
        if line.startswith('when '):
            line_mgr[i : i+1] = [':cond ' + line[5:], ':jf ' + str(i + 3)]
        elif line.startswith('if '):
            line_mgr[i : i+1] = [':cond ' + line[3:], ':jf label' + str(label_counter)]
            # Find the next else or end statement:
            kind, j = find_next_end_else(line_mgr, i + 2)
            if kind == 'end':
                line_mgr[j] = ':label' + str(label_counter)
            else:
                # kind must be an else statement.
                # replace the else statement with a jump:
                else_label = ':label' + str(label_counter)
                label_counter += 1
                line_mgr[j : j+1] = [':j label' + str(label_counter), else_label]
                kind, end = find_next_end_else(line_mgr, j + 1)
                if kind == 'else':
                    throw_exception('MultipleElseStatement',
                                    'if statements cannot have multiple else clauses'
                                    ' (aside from else-if statements).')
                line_mgr[end] = ':label' + str(label_counter)
            label_counter += 1
        elif is_loop(line):
            if line.startswith(':for '):
                # Remove the increment statement, and save it for later use
                increment_statement = line_mgr.pop(i + 1)
                condition_start = 5
            else:
                increment_statement = None
                condition_start = 6
            # label_leave is used to exit the loop:
            label_leave = str(label_counter)
            label_counter += 1
            # label_loop is used to repeat the loop:
            label_loop = str(label_counter)
            label_counter += 1
            # Replace the existing while statement or :for directive with a :cond directive
            line_mgr[i : i+1] = [':cond ' + line[condition_start:], ':jf label' + label_leave, ':label' + label_loop]
            kind, j = find_next_end_else(line_mgr, i + 3)
            if kind == 'end':
                line_mgr[j : j+1] = [':cond ' + line[condition_start:], ':jt label' + label_loop, ':label' + label_leave]
                k = i + 3
                depth = 1
                # stack for keeping track of end statements:
                stack = []
                # Handle 'continue' and 'break' statements:
                while k < j:
                    current = line_mgr[k]
                    if is_loop(current):
                        _, end = find_next_end_else(line_mgr, k + 1, True)
                        depth += 1
                        stack.append(end)
                    elif len(stack) > 0 and current == 'end' and stack[-1] == k:
                        # This is the end to a nested while loop:
                        stack.pop()
                        depth -= 1
                    elif current == 'break ' + str(depth):
                        line_mgr[k] = ':j label' + label_leave
                    elif current == 'continue ' + str(depth):
                        jump_to_loop_start = ':j label' + label_loop
                        if increment_statement is not None:
                            line_mgr[k : k+1] = [increment_statement, jump_to_loop_start]
                        else:
                            line_mgr[k] = jump_to_loop_start
                    k += 1
            else:
                throw_exception('InvalidElseStatement',
                                'While loops cannot have else statements.')
        i += 1
    replace_labels(line_mgr)
