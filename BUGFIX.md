## Pending

- In the REPL, using ``x = 2:3 + 5`` works, but ``x = 5 + 2:3`` does not.
- In the REPL, using ``2 = 5`` does not throw an exception. Moreover, the key-value pair ``{'2': '5'}`` is added to the current environment.

## Fixed

- Statements such as y += y will copy the value of y from earlier frames and dump the result in the latest frame.

```python
    execute_statement('y=9.23', env)
    env.new_frame()
    execute_statement('y+=y', env)
```

Will assign 18.46 to y in the latest frame.

- Executing a statement such as ``y = x+ 19 - 3*6`` succeeds, but ``y = x + 19 - 3*6`` fails, giving an UndefinedVariable exception. Note that the spacing around the ``x`` variable is the source of the problem.