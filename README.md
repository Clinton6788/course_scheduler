# Course Scheduler 

Welcome to the course scheduler. While this was designed for personal use, it can easily be modified for database use (some methods and functions assume future db use), or just used right out of the box. 

## Summary
**This program allows users to create a course schedule, factoring in: GI Bill, grants, user defined restraints, and course prerequisites.**   


### Jump To
- [Developer](#developer)

---
---

## Getting Started

> **NOTE:** If you are NOT an experienced developer, stay on pages: `main.py` and `config > settings.py`!

---

### Non-Developer Type-Hints
> For school's benefit.

On `main.py` and `settings.py`, you will see type-hints for all user fields.  

These show what type of input each field expects:

- `int`: Whole number (e.g. `5`, `-1`)
- `float`: Number with decimals (e.g. `3.75`, `0.0`)
- `str`: Text or characters (e.g. `"Math101"`)
- `list`: Group of items in brackets (e.g. `[1, 2, 3]`, `["A", "B"]`)
- `tuple`: Fixed-size group in parentheses (e.g. `(int, int)` = `(5, 10)`)

---

### Program Use
This program comes with two .csv files for example usage: `course_input_masters.csv` (bachelors and masters courses) and `course_input.csv` (bachelors only). If you want to see how the program works, **keep these in place**. The program is ready to demo out of the box, assuming all dependencies are present. 

1. Install all dependencies. If not comfortable with this, you should not be using this program; it is not a 'refined' program.

2. Either modify `course_input_masters.csv` or `course_input.csv`, or create and save your own course input csv file. I recommend saving to the local directory, then using a relative path (as shown with the example files). 

3. Fill out all settings and user inputs on `main.py` and `settings.py`.

4. Run `main.py`. Everything is setup to take you from input to refined schedule already. Will save schedule in directory as `course_schedule.csv`

---
---

## Developer
For any developer looking to modify and/or improve functionality, this will outline general flow, access points and cautionary areas. Please note that this was developed for personal use and as a school project, so it has not undergone massive refinement and refactoring. It was designed to be fairly modular and easy to adapt to each user/school's situation, as well as easy to integrate with a database (for school use). While it was intended to stay as loosely coupled as possible, the nature of the project resulted in a tighter coupling than I would have liked. 

---

### Caution
It is (generally) an unpolished program, with easy access to settings capable of breaking the function, as well as a very harsh enforcement/validation. Be careful when changing settings. If not comfortable with programming, stick to modifying user inputs on `main.py` and `settings.py` only. 

> **IMPORTANT:** Validation is generally simple `type` enforcement. PROGRAM IS NOT DESIGNED TO HAVE UNTRUSTED INPUT. If using with a database and/or User Input, ensure proper validation of all inputs.

---

### Access and Objects

#### Access

Primary access is currently through `src.services`. While this is redundant in some cases, it limited clutter and allowed for easy to interpret instructions on `main.py`, for the purposes of the school project. 

#### Objects

Listed below are the primary objects and their function.

- User
    - Holds user information, courses, sessions, GI BIll, and user's schedule.
- Restraints
    - Holds user-defined restraints for scheduling. At present, this is not stored with user, but updated/created each new schedule.
- Course
    - Holds course information, calculates self cost upon init
- Session
    - Holds completed and/or scheduled courses, intent (used to define a course user intends on completing either through a transfer credit or 'opt-out' type challenge test) courses. Calculates self cost upon init.
- GIB
    - User's GI BIll. Holds all user GIB data. Calculates benefit charges based on sessions. 

---

### Flow

The general program flow is as follows:

- Intake
    - Collect course input (csv)
    - Clean/validate input
    - Create Course objects
    - Prioritize and sort object
        - Prioritization based on inperson, capstone, and number of prereqs. Used for scheduling later
    - Return prioritized Courses

- Creation
    - New GI Bill created (if necessary)
    - New User created (with courses from intake)

- Scheduling
    - New Restraints obj created
    - All sessions created
    - 'Set' (user defined session number) courses scheduled
    - 'Intent' courses assumed completed for prereq purposes
    - 'Free' courses attempt to be scheduled while respecting restraints
        - Raises `SchedulingError()` if outside restraints or scheduling fails
    - Successful Session objects stored in `user.schedule` as list
        - At present, `session.num` acts as session ID.

- Export
    - User's schedule is listed in csv and saved in dir as `course_schedule.csv`

---
---