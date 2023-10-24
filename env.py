from exception import throw_exception, throw_exception_with_line
from builtin_function import int_div, make_list

import re
import os
import execution
import ast2
import table
import type_tree
import line_manager
import imports

import pretty_print

def normalize_file_name(file_name):
    """
    Normalize the file path, so that different paths which point
    to the same file are just considered 'the same file'.
    A more robust solution would be to use os.path.samefile,
    but this only works on Unix systems for Python 2.x.
    """
    return os.path.normcase(os.path.normpath(file_name))

def get_typed_value(value):
    """
    Retrieve the value contained in a type tuple.
    If not given a tuple, simply returns the value unchanged.
    """
    if type(value) is tuple:
        return value[1]
    return value

def to_read_only(tokens):
    result = []
    for token in tokens:
        if table.hashable(token):
            result.append(token)
        else:
            result.append(None)
    return tuple(result)

class Environment(object):
    """
    A list of frames containing key-value pairs representing variable names
    bound to their values.
    """
    def __init__(self):
        self.frames = [{'null': None, 'true': True, 'false': False,
                        'intDiv': int_div, 'makeList': make_list,
                        '$map': imports.build_map_function(self)}]
        # Save names that shouldn't be replicated in subsequent stack frames
        self.default_names = self.frames[-1].keys()
        self.all_types = type_tree.generate_default_tree()
        self.this_pointers = []
        self.exception_stack = []
        self.last_assigned = None
        self.already_imported = set()
        # The starting directory of the program we are running.
        # This value exists make sure that imports are relative to the
        # Capacita program, not the Python interpreter for Capacita.
        self.starting_dir = None
        # Avoid repeated parsing of an expression by storing expressions
        # in a cache.
        self.expr_cache = {}
        self.indices_cache = {}
        self.line_mgr = None
        self.prgm_counter = 0
        self.is_method_stack = []
        self.lambda_num = 0

    def get_indices(self, tokens):
        ast = ast2.ast_singleton
        cache = self.indices_cache
        read_only_tokens = to_read_only(tokens)
        if read_only_tokens in cache:
            return cache[read_only_tokens]
        indices = ast.collapse_indices(ast.build_indices(tokens))
        cache[read_only_tokens] = indices
        return indices

    def get_tokens(self, expr):
        # Because tokens is a list that is often mutated,
        # it is necessary to make a shallow copy of tokens
        # when reading from the cache.
        if expr in self.expr_cache:
            return (self.expr_cache[expr])[:]
        ast = ast2.AST(expr)
        tokens = ast.parse()
        self.expr_cache[expr] = tokens
        return tokens[:]

    def merge(self, dictionary):
        for key in dictionary:
            self.frames[-1][key] = dictionary[key]
    
    def merge_type_tree(self, new_types):
        current_tree = self.all_types['Object']
        new_tree = new_types['Object']
        self.all_types = type_tree.build_type_table(type_tree.merge_trees(current_tree, new_tree))

    def extract(self, dictionary):
        for key in dictionary:
            if key not in ['$hooks', '$type']:
                self.frames[-1][key] = dictionary[key]

    def get_last_assigned(self):
        return self.last_assigned
    
    def exception_push(self, prgm_counter):
        self.exception_stack.append(prgm_counter)
    
    def exception_pop(self):
        if len(self.exception_stack) == 0:
            return None
        return self.exception_stack.pop()
    
    def new_this(self, obj):
        self.this_pointers.append(obj)
    
    def last_this(self):
        # A 'this' object should not be used if we are in a non-method function
        if len(self.is_method_stack) > 0 and self.is_method_stack[-1] and len(self.this_pointers) > 0:
            return self.this_pointers[-1]
        return {}
    
    def pop_this(self):
        if len(self.this_pointers) > 0:
            return self.this_pointers.pop()
        return {}
    
    def new_frame(self):
        self.frames.append({})

    def typed_assign(self, assign_data, value):
        kind = assign_data.kind
        var = assign_data.var
        frame_or_this = self.get_frame_or_this(var)
        if var in frame_or_this:
            type_tuple = frame_or_this[var]
            if type(type_tuple) is tuple:
                existing_kind = type_tuple[0]
                if kind != existing_kind:
                    self.throw_exception('AlreadyRestrictedType', var + ' already has type ' + existing_kind)
            else:
                self.throw_exception('AlreadyAnyType',
                    var + ' already has type Any and cannot be further restricted.')
        frame_or_this[var] = (kind, value)

    def index_assign(self, assign_data, value):
        index = execution.eval_parentheses(assign_data.suffixes[0].ref, self)
        indexable = assign_data.var
        frame_or_this = self.get_frame_or_this(indexable)
        container = frame_or_this[indexable]
        if type(container) is tuple:
            # Modify the iterable contained within the tuple
            iterable = container[1]
            iterable[index] = value
        else:
            # This iterable has no type restriction
            frame_or_this[indexable][index] = value

    def attr_assign(self, assign_data, value):
        # Check for a type restriction, and enforce that restriction.
        # If the object attribute doesn't exist yet, or has no type restriction
        # in its current value, allow the new value to be assigned.
        # If the type restriction is already in place, make sure to keep
        # the restriction alongside the new value.
        # Otherwise, throw an exception.
        obj_name = assign_data.var
        attr = assign_data.suffixes[0].ref
        frame_or_this = self.get_frame_or_this(obj_name)
        obj_reference = get_typed_value(frame_or_this[obj_name])
        kind = None
        if attr in obj_reference:
            existing_value = obj_reference[attr]
            if type(existing_value) is tuple:
                existing_kind = existing_value[0]
                if not self.value_is_a(value, existing_kind):
                    self.throw_exception('MismatchedType', str(value) + ' is not of type ' + existing_kind)
                kind = existing_kind
        if kind is None:
            obj_reference[attr] = value
        else:
            obj_reference[attr] = (kind, value)

    def simple_assign(self, assign_data, value):
        var_name = assign_data.var
        frame_or_this = self.get_frame_or_this(var_name)
        if var_name in frame_or_this and type(frame_or_this[var_name]) is tuple:
            # There is an existing type restriction
            kind = frame_or_this[var_name][0]
            if not self.value_is_a(value, kind):
                self.throw_exception('MismatchedType', str(value) + ' is not of type ' + kind +
                    '\nType tree is: ' + str(self.all_types))
            frame_or_this[var_name] = (kind, value)
        else:
            # There is no type restriction given
            frame_or_this[var_name] = value

    def assign(self, var_name, value):
        self.last_assigned = value
        if isinstance(var_name, line_manager.AssignmentData):
            assign_data = var_name
            if assign_data.kind is not None:
                self.typed_assign(assign_data, value)
            elif len(assign_data.suffixes) > 0:
                first = assign_data.suffixes[0]
                if first.kind == 'INDEX':
                    self.index_assign(assign_data, value)
                elif first.kind == 'ATTR':
                    self.attr_assign(assign_data, value)
                else:
                    throw_exception('InvalidAssignSuffixKind', first.kind)
            else:
                self.simple_assign(assign_data, value)
            return assign_data
        # Check for a type restriction
        match_obj = re.match(r'([A-Za-z_][A-Za-z_0-9]*) (\$?[A-Za-z_][A-Za-z_0-9]*)', var_name)
        if match_obj:
            kind = match_obj.group(1)
            if not self.value_is_a(value, kind):
                self.throw_exception('MismatchedType', str(value) + ' is not of type ' + kind +
                                     '\nType tree is: ' + str(self.all_types))
            var = match_obj.group(2)
            assign_data = line_manager.AssignmentData(kind, var, [])
            self.typed_assign(assign_data, value)
            return assign_data
        else:
            # Is this an assignment to an index?
            match_obj = re.match(r'(\$?[A-Za-z_][A-Za-z_0-9]*)\[(.+)\]', var_name)
            if match_obj:
                indexable = match_obj.group(1)
                index_expr = match_obj.group(2)
                assign_data = line_manager.AssignmentData(
                    None, indexable, [line_manager.SuffixData('INDEX', index_expr)]
                )
                self.index_assign(assign_data, value)
                return assign_data
            else:
                # Is this an attribute of an object?
                match_obj = re.match(r'(\$?[A-Za-z_][A-Za-z_0-9]*)\.(\$?[A-Za-z_][A-Za-z_0-9]*)', var_name)
                if match_obj:
                    obj_name = match_obj.group(1)
                    attr = match_obj.group(2)
                    assign_data = line_manager.AssignmentData(
                        None, obj_name, [line_manager.SuffixData('ATTR', attr)]
                    )
                    self.attr_assign(assign_data, value)
                    return assign_data
                else:
                    assign_data = line_manager.AssignmentData(None, var_name, [])
                    self.simple_assign(assign_data, value)
                    return assign_data

    # TODO : rework how hooks operate. Most environment frames will not
    # need a '$hooks' attribute anymore, since functions now carry their own hooks.
    def assign_hook(self, func_name, value):
        frame_or_this = self.get_frame_or_this(func_name)
        if '$hooks' not in frame_or_this:
            frame_or_this['$hooks'] = {}
        frame_or_this['$hooks'][func_name] = value
        # Return a reference to the current pool of hooks.
        return frame_or_this['$hooks']

    def activate_hook(self, func_name, supplied_hooks):
        if supplied_hooks is not None:
            # All function bodies carry their own hooks.
            self.assign(func_name, supplied_hooks[func_name])
        else:
            # Top level code that is not wrapped in a function body
            # uses the old style of activating hooks
            frame_or_this = self.get_frame_or_this_with_hook(func_name)
            self.assign(func_name, frame_or_this['$hooks'][func_name])

    def has_hook(self, func_obj):
        """
        Returns True if the function object has been defined by
        a 'sub' or 'func' statement in the current scope.
        Returns False if the function object was created by other means.
        (e.g. a function that was passed in as an argument, or
              generated by another function such as 'compose(f, g)'
              is considered 'created by other means'.)
        """
        # TODO : we assume any existing hook will reside in env.last()
        # However, this may cause issues if the hook resides in
        # env.last_this() instead.
        last_frame = self.last()
        if '$hooks' not in last_frame:
            return False
        return func_obj in last_frame['$hooks'].values()

    def get_frame_or_this_with_hook(self, func_name):
        last_this = self.last_this()
        if '$hooks' in last_this and func_name in last_this['$hooks']:
            return last_this
        return self.frames[-1]

    def get_frame_or_this(self, var_name):
        last_this = self.last_this()
        if var_name in last_this:
            return last_this
        return self.frames[-1]
    
    def update(self, var_name, value):
        # TODO : env.update(...) should be removed in favor
        # of transforms such as (age += 1) -> (age = age + 1)
        # Therefore the added functionality of env.assign(...)
        # will apply to these statements.
        if var_name in self.frames[-1]:
            self.frames[-1][var_name] = value
        else:
            self.throw_exception('UndefinedVariable', var_name + ' is not defined.')

    def update_numeric(self, var_name, added_value):
        """
        Update an existing variable containing a numeric value.
        Used for increment and decrement operators.
        """
        target_frame = self.get_frame_or_this(var_name)
        if var_name in target_frame:
            value = target_frame[var_name]
            if type(value) is tuple:
                kind, val = value
                target_frame[var_name] = (kind, val + added_value)
            else:
                target_frame[var_name] += added_value
        else:
            self.throw_exception('UndefinedVariable', var_name + ' is not defined.')

    def get(self, var_name):
        if var_name == 'input':
            # Read a line from the console
            return '"{0}"'.format(raw_input())
        last_this = self.last_this()
        if var_name in last_this:
            return get_typed_value(last_this[var_name])
        i = -1
        while i >= -len(self.frames):
            if var_name in self.frames[i]:
                value = self.frames[i][var_name]
                return get_typed_value(value)
            else:
                i -= 1
        # If this variable is not defined, look in the type tree:
        if var_name in self.all_types:
            return self.all_types[var_name]
        self.throw_exception('UndefinedVariable', var_name + ' is not defined.')
        
    def has_name(self, var_name):
        """
        Returns True if env.get(var_name) would succeed, otherwise False.
        """
        if var_name in self.last_this():
            return True
        i = -1
        while i >= -len(self.frames):
            if var_name in self.frames[i]:
                return True
            else:
                i -= 1
        if var_name in self.all_types:
            return True
        return False
        
    def pop(self):
        return self.frames.pop()
    
    def last(self):
        return self.frames[-1]

    def merge_latest(self, other_env):
        latest_frame = other_env.frames[-1]
        for var, value in latest_frame.items():
            if var not in self.default_names:
                self.assign(var, value)
            
    def copy(self):
        """
        Provides a deep copy of the current environment.
        """
        new_env = Environment()
        new_frames = []
        for frame in self.frames:
            new_frames.append({k: v for k, v in frame.items()})
        new_env.frames = new_frames
        return new_env
        
    def value_is_a(self, value, wanted_kind):
        kind = type_tree.get_type(value)
        if wanted_kind not in self.all_types:
            return False
        tree = self.all_types[wanted_kind]
        return tree.categorizes(kind)
    
    def new_type(self, parents, child):
        child_tree = type_tree.TypeTree(child)
        self.all_types[child] = child_tree
        for parent in parents:
            parent_tree = self.all_types[parent]
            parent_tree.add_subclass(child_tree)
    
    def has_starting_dir(self):
        return self.starting_dir is not None
    
    def add_import(self, file_name):
        if not self.has_starting_dir():
            # No files have been imported. Set the starting directory.
            self.starting_dir = os.path.dirname(file_name)
        normalized_file_name = normalize_file_name(file_name)
        self.already_imported.add(normalized_file_name)
    
    def is_already_imported(self, file_name):
        return normalize_file_name(file_name) in self.already_imported
    
    def set_correct_directory(self, file_name):
        if not self.has_starting_dir():
            return file_name
        return os.path.join(self.starting_dir, file_name)

    def pretty_print(self):
        """
        Displays all variables in all frames in a human readable format.
        """
        pretty_print.pretty_print(self.frames)

    def throw_exception(self, kind, msg):
        throw_exception_with_line(kind, msg, self.line_mgr, self.prgm_counter)

    def __repr__(self):
        return str(self.frames)

    def __str__(self):
        return repr(self)
