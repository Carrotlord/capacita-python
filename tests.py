import capacita
import time
import os
import fileio

import type_tree
import exception

def make_artificial_input(lines):
    state = {'line_num': 0}
    length = len(lines)
    def artificial_input(prompt):
        i = state['line_num']
        if i < length:
            line = lines[i]
            #print prompt + line
            state['line_num'] += 1
            return line
        return 'exit()'
    return artificial_input

def test_program(contents, use_repl):
    if use_repl:
        lines = contents.splitlines()
        input_function = make_artificial_input(lines)
        capacita.repl(existing_env=None, get_input=input_function)
    else:
        capacita.execute_program(contents)

def test_all(path, has_delay=True, use_repl=False):
    files = [f for f in os.listdir(path) if f.endswith('.cap')]
    print '===== Starting tests...'
    is_first_file = True
    for file in files:
        if has_delay and not is_first_file:
            time.sleep(3)
        is_first_file = False
        full_path = path + '/' + file
        print '===== Testing ' + full_path
        contents = fileio.file_to_str(full_path)
        try:
            test_program(contents, use_repl)
        except NameError as ex:
            exception.throw_exception('UnexpectedNameError', str(ex))
        except BaseException as ex:
            print '===== Exception: ' + str(ex.__class__)
    print '===== Done.'

def test_file(path, use_repl=False):
    contents = fileio.file_to_str(path)
    test_program(contents, use_repl)

def test_tree_merge():
    a = type_tree.TypeTree('A')
    b = type_tree.TypeTree('B')
    c = type_tree.TypeTree('C')
    g = type_tree.TypeTree('G')
    b.add_subclass(g)
    a.add_subclass(b)
    a.add_subclass(c)
    a2 = type_tree.TypeTree('A')
    d = type_tree.TypeTree('D')
    b2 = type_tree.TypeTree('B')
    e = type_tree.TypeTree('E')
    f = type_tree.TypeTree('F')
    b2.add_subclass(e)
    b2.add_subclass(f)
    a2.add_subclass(d)
    a2.add_subclass(b2)
    print a.format()
    print a2.format()
    merged = type_tree.merge_trees(a, a2)
    print merged.format()
    print type_tree.build_type_table(merged)
    