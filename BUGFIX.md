## Pending

- In the REPL, using ``2 = 5`` does not throw an exception. Moreover, the key-value pair ``{'2': '5'}`` is added to the current environment.
- Expressions such as ``x = 5; print 5 * -x`` do not work unless wrapped in parentheses: ``5 * (-x)``
- Booleans can be compared with ``>`` and ``<``, such as ``true > false``, which should throw an exception instead. Note that in Python, ``True > False`` resolves to ``True``.
- Dissimilar types can be compared, such as ``2 < "hello"`` resolving to ``true``. This should throw an exception instead. This is due to a quirk of Python 2.x allowing dissimilar comparisons.

## Fixed

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