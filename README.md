# Class Scheduler 

Welcome to the class scheduler. While this was designed for personal use, it can easily be modified, or even used right out of the box. 

## Summary
**This program allows users to create a course schedule, factoring in: GI Bill, user defined restraints, prerequisites and user defined priorities.**   

---

### A Note of Caution
It is (generally) an unpolished program, with easy access to settings capable of breaking the function, as well as a very harsh enforcement/validation. Be careful when changing settings, and operate through the CLI unless comfortable. It was designed to be fairly modular and easy to adapt to each user's and school's situation, as well as easy to integrate with a database (for school use). Most classes are coupled loosely, if at all. 

> **IMPORTANT:** Validation is generally simple `type` enforcement. PROGRAM IS NOT DESIGNED TO HAVE UNTRUSTED INPUT. If using with a database and/or FE, ensure proper validation of all inputs.

---
---

## User Stories
**As a user, I want to be able to...**
- Import classes from .csv or add classes manually
    - Stores in SQLite
- Import in-person classes from .csv or add in-person classes manually
    - Stores in SQLite
    - Have a unique list that changes every semester/session
        - Based on Location
- View all currently completed classes
- View all currently enrolled classes
- View by session
- Enter GI Bill benefits start, end dates and Total Coverage Amount
- Have the GI Bill benefits update based on what's completed, when it was completed and remaining benefits
- Have the ability to mark classes as 'Transfer Credit'
    - Does not mean completed, only intent to complete in Sophia
    - This removes course from session and cost projections
    - Fits into session that allows for pre-req satisfaction
- See an estimated course schedule that accounts for:
    - Transfers (Not included in enrollment, but IS included in pre-req and completion date)
    - Pre-reqs
    - Remaining GI Bill benefits
    - In-person (Where applicable)
- Be able to move courses to adjust schedule
    - Auto adjusts costs, pre-reqs, remaining schedule, etc.
- Download .csv with tentative schedule and course details

## Flow
### Intake/Org
- `get_excel()`
    - Data imported and cleand from CSV/EXCEL; converted to dataframe
- `df` returned
- `create_courses(df)`
    - Course objects created from rows
- `all_courses` LIST returned
- `organize_courses(all_courses)`
    - Seperates into 'Level' (grad, undergrad)
    - Returned data structure `{LevelENUM.value: {Course.course_id: Course,...},...}`
- `course_level_dict` returned
- `for k,v in course_level_dict:`
    - Iter through to get individual level dicts
    - `prioritize_courses(v)`
        - Assigns and orders by course priority
        - `ordered_courses` LIST returned
    - `filter_courses(ordered_courses)`
        - filters based on CourseFilterEnum
        - Returns: `{CourseFilterENUM.value: [Course,...],...}`
    - `filtered_course_dict` returned
    - `course_level_dict[k] = filtered_course_dict`