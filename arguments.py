from exception import throw_exception
from execution import eval_parentheses

def is_grouping_argument(arg_name):
    return arg_name.startswith('[') and arg_name.endswith(']')

def count_grouping_arguments(arg_names):
    count = 0
    for name in arg_names:
        if is_grouping_argument(name):
            count += 1
    return count

def is_out_of_bounds(index, lst):
    list_len = len(lst)
    return index >= list_len or index < -list_len

def assign_arguments(arg_names, arg_values, env):
    num_grouping_args = count_grouping_arguments(arg_names)
    if num_grouping_args == 0:
        if len(arg_values) > len(arg_names):
            throw_exception('TooManyArgumentsException',
                            'Number of arguments exceeds number expected in function definition')
        for i in xrange(len(arg_names)):
            current_name = arg_names[i]
            if '=' in current_name:
                # This argument name has a default value given
                # TODO : the following line does not account for operators
                # such as ==, !=, <=, etc.
                pieces = [piece.strip() for piece in current_name.split('=')]
                if len(pieces) != 2:
                    throw_exception('DefaultArgumentException',
                                    'Incorrect default argument syntax in {0}'.format(current_name))
                var_name, var_expr = pieces
                if is_out_of_bounds(i, arg_values):
                    env.assign(var_name, eval_parentheses(var_expr, env))
                else:
                    # Instead of the default value, use the value already given
                    env.assign(var_name, arg_values[i])
            else:
                if is_out_of_bounds(i, arg_values):
                    throw_exception('ArgValueException',
                                    'Number of arguments does not match function definition')
                else:
                    env.assign(current_name, arg_values[i])
    elif num_grouping_args == 1:
        for i in xrange(len(arg_names)):
            if is_grouping_argument(arg_names[i]):
                break
        # Remove brackets around group name
        group_name = arg_names[i][1:-1].strip()
        num_left = i
        num_right = len(arg_names) - num_left - 1
        # TODO : account for default arguments
        # (num_left + num_right) might be greater than the actual number of needed arguments
        if len(arg_values) < num_left + num_right:
            throw_exception('TooFewArgumentsException',
                            'Number of arguments is less than number expected in function definition')
        else:
            values_for_left = arg_values[0:i]
            if num_right == 0:
                values_for_right = []
                values_for_middle = arg_values[i:]
            else:
                values_for_right = arg_values[-num_right:]
                values_for_middle = arg_values[i:-num_right]
            env.assign(group_name, values_for_middle)
            other_arg_names = arg_names[0:i] + arg_names[i+1:]
            assign_arguments(other_arg_names, values_for_left + values_for_right, env)
    else:
        throw_exception('GroupingArgumentException',
                        'Cannot have more than 1 grouping argument in function definition')
