# 🎓 Course Scheduler

Welcome to the **Course Scheduler**!  
This tool was developed for personal and academic use, but can be extended for database integration or used directly out of the box.

---

## Summary

This program allows users to create a course schedule while accounting for:

- GI Bill eligibility
- Grants and benefit use
- User-defined restraints
- Course prerequisites
- Intent to transfer or challenge courses

---

## Jump To

- [Getting Started](#getting-started)
  - [Course Input CSV Format](#-course-input-csv-format)
  - [Notes & Validation Rules](#notes--validation-rules)
  - [Example CSV Row](#example-csv-row)
  - [Non-Developer Type-Hints](#non-developer-type-hints)
  - [Program Use](#program-use)
- [Developer](#developer)
  - [Caution](#caution)
  - [Access and Objects](#access-and-objects)
  - [Program Flow](#flow)

---

##  Getting Started

> **Non-developers:** Stick to editing `main.py` and `config/settings.py`. Everything else assumes some programming familiarity.

---

### Course Input CSV Format

Course data must be provided via a **CSV file**, with the **exact columns** listed below. Each column must follow the specified format and allowed values.

#### Required Columns

| Column Name         | Type     | Description |
|---------------------|----------|-------------|
| `Course ID`         | `str`    | Unique identifier or name of the course. Example: `ENG101` |
| `Credit Hours`      | `int`    | Number of credit hours (e.g. `3`) |
| `Status`            | `int`    | Course status: `0` = Not started, `1` = In Progress, `2` = Completed |
| `Level`             | `int`    | Course level: `0` = Undergraduate, `1` = Graduate |
| `PreReqs`           | `str`    | Prerequisite logic string using pipe (`|`) separators. Items in brackets `[]` are treated as OR conditions. Items outside are treated as AND. <br><br>ℹ️ *Example format is shown in `course_input.csv` (example file included).* |
| `Capstone`          | `bool`   | Capstone course? `0` = No, `1` = Yes. Capstones must be scheduled last. |
| `Session`           | `int`    | Manually assigned session number. Required for `In Progress` or `Completed` courses. Leave blank for `Transfer` or `Challenge` intents or courses that should be auto-scheduled. |
| `Transfer Intent`   | `int`    | Will this be completed via **external transfer**? `0` = No, `1` = Yes |
| `Challenge Intent`  | `int`    | Will this be completed via **school-provided challenge test**? `0` = No, `1` = Yes |

---

### Notes & Validation Rules

- All columns are **required**. Use `0` or leave blank where not applicable.
- `PreReqs` must refer to valid `Course ID`s in the file (or already completed).
- `Session` must be set if `Status` is `1` or `2`.
- If `Transfer Intent` or `Challenge Intent` is `1`, **leave `Session` blank**.
- Capstone courses (`Capstone = 1`) are scheduled **last**, after all prerequisites.

---

### Example CSV Row

```
ENG101,3,2,0,,0,1,0,0
```

| Field              | Value | Explanation |
|--------------------|--------|-------------|
| Course ID          | `ENG101` | Course name |
| Credit Hours       | `3`      | 3 credit hours |
| Status             | `2`      | Completed |
| Level              | `0`      | Undergraduate |
| PreReqs            | *(blank)* | No prerequisites |
| Capstone           | `0`      | Not a capstone |
| Session            | `1`      | Completed in session 1 |
| Transfer Intent    | `0`      | Not a transfer |
| Challenge Intent   | `0`      | Not a challenge |

---

### Save Format

Save your file with a `.csv` extension (e.g. `courses.csv`).  
Use a plain text editor, Excel, or any spreadsheet tool that preserves raw CSV formatting.

---

### Non-Developer Type-Hints

In `main.py` and `settings.py`, you’ll see **type hints** beside input fields. These tell you what kind of value to provide:

- `int`: Whole number (e.g. `3`, `0`)
- `float`: Decimal (e.g. `3.75`)
- `str`: Text or characters (e.g. `"ENG101"`)
- `list`: List of values in square brackets (e.g. `[1, 2, 3]`)
- `tuple`: Fixed-length set in parentheses (e.g. `(5, 10)`)

---

### Program Use

The repo includes example files to test immediately:

- `course_input.csv`: Undergraduate only
- `course_input_masters.csv`: Undergraduate and graduate

To run:

1. Install all Python dependencies.
2. Modify one of the example CSVs or create your own.
3. Set your configuration in `main.py` and `config/settings.py`.
4. Run `main.py`.

Output is saved as `course_schedule.csv` in the working directory.

---
---

## Developer

This section is for developers interested in modifying or extending the scheduler.

### Caution

This is a functional but unpolished tool. The system:

- Allows **easy access to critical settings**
- Has **minimal safety validation**
- Assumes **trusted input only**

If integrating with user input or a database, add your own validation layer.

---

### Access and Objects

#### Primary Access Point

All business logic is routed through `src/services`, designed to reduce clutter in `main.py`.

#### Key Objects

- **`User`**: Holds user data, GI Bill, course list, and schedule.
- **`Restraints`**: Holds constraints like course load per session, max credit hours, etc.
- **`Course`**: Represents a course and calculates its cost.
- **`Session`**: Represents a semester/session, holds courses and calculates cost.
- **`GIB`**: GI Bill handler, calculates benefit usage and charges.

---

### Flow

1. **Intake**
   - Read and validate CSV input
   - Create `Course` objects
   - Prioritize based on capstone, number of prerequisites, etc.

2. **Creation**
   - Create new `User`
   - Create new `GIB` (if needed)

3. **Scheduling**
   - Create `Restraints` object
   - Schedule fixed (manually set) courses first
   - Treat transfer/challenge courses as "completed"
   - Schedule remaining courses within constraints
   - Raise `SchedulingError` if scheduling fails

4. **Export**
   - Output schedule as `course_schedule.csv`

---
