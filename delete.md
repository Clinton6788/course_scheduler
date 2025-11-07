

For full optimization:

- Prioritize all courses
- Create max potential sessions (Level free)
    - On min courses/session and courses count
        - Have bool arg for 'last session in level may have less than min'
- Get targets (level free)

- Attempt to schedule based on existing targets
    - Keep primary in place


    - Call 'adjust_tgts' if too many


Schedule session:
- schedule all set courses
- get targets for an even spread
    - Have 'Load preference'
        - level, front/rear
- Attempt to schedule
    - Have call with solution and recursion:
        ```python
        recur = 0
        suc, new_tgt = schedule_all(orig_args, tgts)
        if not suc:
            recur += 1
            if recur < MAX_RECUR:
                schedule_all(orig_args, new_tgt)
            else:
                HIT RECURSION LIMIT
        ```

### Solution for target manipulation


- Update schedule free to reflect return of potentially NEW User Object

## Target Object

- Target lists by level
- Historical layouts