import builtin_method
import execution

method_names = {
    ':': 'ratio',
    '^': 'pow',
    '*': 'mul',
    '/': 'div',
    '%': 'mod',
    '+': 'plus',
    '-': 'minus',
    '==': 'eq',
    '!=': 'notEq',
    '>=': 'greaterEq',
    '<=': 'lesserEq',
    '>': 'greater',
    '<': 'lesser',
    ' and ': 'and',
    ' or ': 'or',
    ' xor ': 'xor'
}

unary_method_names = {
    '-': 'negative',
    'not ': 'not'
}

def ready_for_overload(op, left, right):
    left_is_obj = type(left) is dict
    right_is_obj = type(right) is dict
    # At least one operand needs to be a user-defined object.
    if (not left_is_obj) and (not right_is_obj):
        return False
    # == and != already have default behavior
    # (e.g. comparing an object to null, as in 'obj == null', should
    #  automatically work)
    # Only allow an operator overload to happen if $eq or $notEq
    # methods are defined.
    if op in ['==', '!=']:
        base_name = method_names[op]
        method_name = '$' + base_name
        if left_is_obj and method_name in left:
            return True
        reflected_method_name = '$r' + base_name
        if right_is_obj and reflected_method_name in right:
            return True
        return False
    return True

def run_method(method_name, env, primary_obj, secondary_obj=None):
    method = builtin_method.dot_operator(primary_obj, method_name, env)
    # TODO : secondary_obj could be 'null' in Capacita, which maps to 'None' in
    # Python. This may cause an issue when a method is supposed to be called
    # as obj.method(null) instead of just obj.method()
    if secondary_obj is None:
        method_args = []
    else:
        method_args = [secondary_obj]
    return method.execute(method_args, env)

def operator_overload(op, left, right, idx, tokens, env):
    result = {'return_val': None, 'is_unary': None}
    if type(left) is dict:
        result['return_val'] = run_method('$' + method_names[op], env, left, right)
        result['is_unary'] = False
    else:
        # 'right' is a dictionary
        is_unary = execution.is_unary(tokens, idx)
        result['is_unary'] = is_unary
        if is_unary:
            result['return_val'] = run_method('$' + unary_method_names[op], env, right)
        else:
            # Reflected method
            result['return_val'] = run_method('$r' + method_names[op], env, right, left)
    return result
