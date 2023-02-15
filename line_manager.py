import prepare_program
import exception

def is_assignment_statement(line):
    i = 0
    length = len(line)
    # The operators !=, >=, and <= start with !, >, or <
    starters = '!><'
    in_quotes = False
    while i < length:
        if prepare_program.is_quote(line, i):
            in_quotes = not in_quotes
        if not in_quotes:
            current_char = line[i]
            if current_char == '=':
                if i == 0 or i == length - 1:
                    throw_exception(
                        'SyntaxError',
                        'Statement begins or ends with an equals sign: ' + line
                    )
                elif line[i + 1] == '=':
                    # Double equals sign. Skip the next character.
                    i += 1
                elif line[i - 1] not in starters:
                    # This must be an assignment statement.
                    return True
        i += 1
    return False

def is_statement(query):
    """Returns True if query is a statement, else False."""
    if query.startswith('print ') or query.startswith('show ') or \
       query.startswith('return ') or query.startswith(':') or \
       query == 'try' or query == 'end' or query == 'else' or \
       query.startswith('throw ') or query.startswith('catch ') or \
       query.startswith('super ') or query.startswith('import ') or \
       query.startswith('func '):
        return True
    return is_assignment_statement(query)

def normalize_slice(slice_obj, sequence):
    length = len(sequence)
    start = 0
    stop = length
    step = 1
    if slice_obj.start is not None:
        start = slice_obj.start
    if start < 0:
        start += length
    if slice_obj.stop is not None and slice_obj.stop < stop:
        stop = slice_obj.stop
    if stop < 0:
        stop += length
    return slice(start, stop, step)

class LineData(object):
    def __init__(self, line, start_line, end_line=None):
        self.line = line
        self.line_num = start_line
        self.is_statement = False
        if end_line is None:
            self.end_line_num = start_line
        else:
            self.end_line_num = end_line

    def modify_line(self, function):
        self.line = function(self.line)

class AssignmentData(object):
    def __init__(self, kind, var, suffixes):
        if kind is not None and suffixes != []:
            exception.throw_exception(
                'TypeRestrictionNotApplied',
                ('Type {0} cannot be applied to {1} ' +
                 'when it has attributes or indices: {2}').format(
                     kind, var, suffixes
                 )
            )
        self.kind = kind
        self.var = var
        self.suffixes = suffixes

class SuffixData(object):
    def __init__(self, kind, ref):
        self.kind = kind
        self.ref = ref

class LineManager(object):
    def __init__(self, original_lines):
        self.internal_lines = []
        for line_num, line in enumerate(original_lines):
            self.internal_lines.append(LineData(line, line_num))
        self.last_start_index = -1
        self.last_stop_index = -1

    def set_last_indices(self, start, stop):
        self.last_start_index = start
        self.last_stop_index = stop

    def __getitem__(self, index):
        if type(index) is slice:
            results = self.internal_lines[index]
            return [line_data.line for line_data in results]
        return self.internal_lines[index].line

    def __setitem__(self, index, content):
        if type(index) is slice:
            index = normalize_slice(index, self.internal_lines)
            line_num = self.internal_lines[index.start].line_num
            end_line_num = self.internal_lines[index.stop - 1].line_num
            new_slice_content = [LineData(line, line_num, end_line_num) for line in content]
            self.internal_lines[index] = new_slice_content
        else:
            line_num = self.internal_lines[index].line_num
            end_line_num = self.internal_lines[index].end_line_num
            self.internal_lines[index] = LineData(content, line_num, end_line_num)
        self.set_last_indices(line_num, end_line_num)

    def get_line_data(self, index):
        return self.internal_lines[index]

    def subset(self, start, stop):
        new_line_mgr = LineManager([])
        new_line_mgr.internal_lines = self.internal_lines[start : stop]
        return new_line_mgr

    def insert(self, index, line):
        self.internal_lines.insert(index, LineData(line, self.last_start_index, self.last_stop_index))

    def append_line_data(self, line_data):
        self.internal_lines.append(line_data)

    def enumerate_line_data(self):
        return enumerate(self.internal_lines)

    def pop(self, index=None):
        if index is None:
            return self.internal_lines.pop().line
        return self.internal_lines.pop(index).line

    def format_lines(self):
        # All functions act as if they had 'return null' as the final statement
        return str(tuple(self.get_lines() + ['return null']))

    def __len__(self):
        return len(self.internal_lines)

    def for_each_line(self, function):
        for line_data in self.internal_lines:
            line_data.modify_line(function)

    def get_lines(self):
        return [line_data.line for line_data in self.internal_lines]

    def classify_statements(self):
        for line_data in self.internal_lines:
            line_data.is_statement = is_statement(line_data.line)

    def has_nothing(self):
        return all(line == '' for line in self)

    def drop_empty(self):
        new_lines = []
        for line, data in zip(self, self.internal_lines):
            if line != '':
                new_lines.append(data)
        self.internal_lines = new_lines

    def display(self):
        num_digits = 1
        for i, line_data in enumerate(self.internal_lines):
            stmt_kind = 'stmt' if line_data.is_statement else 'expr'
            if line_data.line_num == line_data.end_line_num:
                print '({0}) {1}: {2} {3} | {4}'.format(
                    stmt_kind,
                    i,
                    line_data.line_num,
                    ' ' * num_digits,
                    line_data.line
                )
            else:
                print '({0}) {1}: {2}-{3} | {4}'.format(
                    stmt_kind,
                    i,
                    line_data.line_num,
                    line_data.end_line_num,
                    line_data.line
                )
                num_digits = len(str(line_data.end_line_num))
