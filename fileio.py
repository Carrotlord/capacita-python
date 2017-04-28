def file_to_str(file_name):
    """Returns contents of a text file as a string."""
    file_obj = open(file_name, 'r')
    contents = file_obj.read()
    file_obj.close()
    return contents
