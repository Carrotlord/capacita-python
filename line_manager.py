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
        if end_line is None:
            self.end_line_num = start_line
        else:
            self.end_line_num = end_line

class LineManager(object):
    def __init__(self, original_lines):
        self.internal_lines = []
        for line_num, line in enumerate(original_lines):
            self.internal_lines.append(LineData(line, line_num))

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

    def __len__(self):
        return len(self.internal_lines)

    def display(self):
        num_digits = 1
        for i, line_data in enumerate(self.internal_lines):
            if line_data.line_num == line_data.end_line_num:
                print '{0}: {1} {2} | {3}'.format(i, line_data.line_num, ' ' * num_digits, line_data.line)
            else:
                print '{0}: {1}-{2} | {3}'.format(i, line_data.line_num, line_data.end_line_num, line_data.line)
                num_digits = len(str(line_data.end_line_num))
