import capacita
import time
import os
import fileio

def test_all(path, has_delay=True):
    files = [f for f in os.listdir(path) if f.endswith('.cap')]
    print '===== Starting tests...'
    for file in files:
        if has_delay:
            time.sleep(3)
        full_path = path + '/' + file
        print '===== Testing ' + full_path
        contents = fileio.file_to_str(full_path)
        try:
            capacita.execute_program(contents)
        except BaseException as ex:
            print '===== Exception: ' + str(ex.__class__)
    print '===== Done.'
