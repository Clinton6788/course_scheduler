import src.services as ser
import datetime as dt
"""This program is setup with some provided constants to see operations.
If modifying for DB usage, match naming conventions here.
"""

"""---------User-----------"""
# User ID (Any | None). Pass `None` for generated shortuuid
USER_ID = "User1"
# Dollar amount of grants per session (float)
TOTAL_GRANT_AMOUNT_PER_SESSION = 

"""--------User GI Bill ----------
If no GI Bill, leave blank and Comment out line ... below."""

# Total Dollar coverage for GI Bill Annual Coverage (float)
YEARLY_GIB_AMOUNT = 

# Month, day the benefit year starts (tuple[int, int])
BENEFIT_YEAR_START = 

# Remaining benefit days as Month, Day (tuple[int, int])
BENEFITS_REMAINING = 

# Date `BENEFITS_REMAINING` was updated. (dt.date)
# dt.date(<year>,<month>,<day>)
BENEFITS_ASOF = dt.date()

"""---------- INPUT ------------
Input path for user courses. Input is a .csv with columns:
[Course ID, Credit Hours, Status, Level, PreReqs, Capstone, Session, Transfer Intent,
Challenge Intent]

To see all possible name variations, see intake.py
"""

# Path to csv
INPUT_PATH = "course_input.csv"
# Absoloute or relative path
ABSOLOUTE_PATH = False

ser.create_gib()