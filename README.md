# Class Scheduler 

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