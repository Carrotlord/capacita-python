## Pending

- In the REPL, using ``2 = 5`` does not throw an exception. Moreover, the key-value pair ``{'2': '5'}`` is added to the current environment.
- Expressions such as ``x = 5; print 5 * -x`` do not work unless wrapped in parentheses: ``5 * (-x)``
- Booleans can be compared with ``>`` and ``<``, such as ``true > false``, which should throw an exception instead. Note that in Python, ``True > False`` resolves to ``True``.
- Dissimilar types can be compared, such as ``2 < "hello"`` resolving to ``true``. This should throw an exception instead. This is due to a quirk of Python 2.x allowing dissimilar comparisons.
- Expressions such as ``[[1,2][3,4]]`` are transformed into ``[[1, 2], [3, 4]]``.
- Since objects can now refer to themselves with ``this``, there might be cases where the user performs ``return this``, which will have unexpected behavior because this is also the way new objects are generated.
- Methods called on list literals such as ``[1,2,3].pop()`` do not work.
- Strings such as ``'\\'`` and ``"\\"`` do not work.
- A single quote in a comment causes an error.
- Attempting an expression such as ``(3.0 * 10 ^ 20) + 1`` fails, while ``3.0 * 10 ^ 20 + 1`` succeeds. Note that this has to do with parenthetical evaluation and how very large (or very small) floats are formatted with an exponent (such as ``3e+20`` or ``3e-20``).

## Fixed

- Direct list concatenation no longer works.

- Operators cannot be embedded in strings without causing in error. For instance, ``"this and that"`` (operator boolean ``and``) as well as ``"two + three"`` (operator ``+``).

- Statements such as y += y will copy the value of y from earlier frames and dump the result in the latest frame.

```python
    execute_statement('y=9.23', env)
    env.new_frame()
    execute_statement('y+=y', env)
```

Will assign 18.46 to y in the latest frame.

- Executing a statement such as ``y = x+ 19 - 3*6`` succeeds, but ``y = x + 19 - 3*6`` fails, giving an UndefinedVariable exception. Note that the spacing around the ``x`` variable is the source of the problem.

- In the REPL, using ``x = 2:3 + 5`` works, but ``x = 5 + 2:3`` does not.

- Negative numerical literals do not work. (e.g. -2)

- Certain negative expressions do not work, such as ``-(-3)`` and ``x = 5; print -x``. This is because only negative signs at the front of a token list or which go after another operator are properly handled.

- Expressions such as ``5 * -3`` do not work unless wrapped in parentheses: ``5 * (-3)``

- Function composition brings up the following bug:

```
func = compose(mulHalf, add5)
func2 = compose(add5, mulHalf)
func3 = compose(square, add5)
func4 = compose(square, square)
print func(10)
print func2(10)
print func3(10)
print func4(10)
```

In this case, all calls to func through func4 will act like func4, returning 10000.

- Using ``"("`` as a string literal does not work. It is interpreted as a parenthetical expression.
