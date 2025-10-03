import src.services as ser
import datetime as dt
"""This program is setup with some provided constants to see operations.
If modifying for DB usage, match naming conventions here.
"""

"""------------------------------ Start User Input ---------------------------------"""

"""---------User-----------"""
# User ID (Any | None). Pass `None` for generated shortuuid
USER_ID = "User1"

# Dollar amount of grants per session (float)
TOTAL_GRANT_AMOUNT_PER_SESSION = 2099.0

# Start Date of first session (dt.date)
# Year and month and day should be TARGET start. 
# If session is May start, but technically starts Apr 25,
# FIRST_SESSION_DATE should be: `dt.date(<year>, 5, 1)`, representing May 1.
FIRST_SESSION_DATE = dt.date(2025, 5, 1)

"""--------User GI Bill ----------"""
# If no GI Bill, pass each `None`.

# Total Annual Dollar coverage for GI Bill (float)
YEARLY_GIB_AMOUNT = 27120.0

# Month, day the benefit year starts (tuple[int, int])
BENEFIT_YEAR_START = (8, 1)

# Remaining benefit days as Month, Day (tuple[int, int])
BENEFITS_REMAINING = (23, 10)

# Date `BENEFITS_REMAINING` was updated. (dt.date)
# dt.date(<year>,<month>,<day>)
BENEFITS_ASOF = dt.date(2025, 8, 27)

"""---------- INPUT ------------"""
# Input path for user courses. 
# Input is a .csv with all columns listed in README.
# To see all possible column name variations, see intake.py. 
# To see column values/names, see README.

# Path to csv (Use `course_input` for undergrad, `course_input_masters` for graduate)
INPUT_PATH = "course_input_masters.csv"

# Absoloute or relative path
ABSOLOUTE_PATH = False


"""-----------OUTPUT-----------"""
# Output for schedule

# Type of output **AT PRESENT ONLY CSV SUPPORTED** (str)
OUTPUT_TYPE = "csv"

# Path for output (str)
OUTPUT_PATH = "course_schedule.csv"

# Realative or Absouloute Path for OUTPUT_PATH (bool)
OUTPUT_ABS = False

"""------- SCHEDULING RESTRAINTS ------"""
# Used to create a Restraints object for scheduling.

# **IF FILLING OUT INPERSON, FILL OUT ALL INSIDE `region InPerson`

# region InPerson ------------------------

# List of inperson courses as String course_id (list['ENGL112',...])
INPERSON_COURSES = [

]

# Inperson End Date - Date the in-person offerings are no longer available (dt.date | None)
# If INPERSON_COURSES, MUST be dt.date() instance, else MUST be None.
INPERSON_END_DT = None

# Minimum inperson courses per session. This is treated as a HARD limit. Optional. (int | None)
MIN_INPERSON = 1

# Maximum inperson courses per session. This is treated as a SOFT limit. Optional. (int | None)
MAX_INPERSON = 1

# endregion --------------------------------

# Max cost **TO USER** for each session. cost is calculated after grants and GI BIll. Optional. (float | None)
SES_MAX_COST = None

# Minimum courses per session for scheduling. Treated as HARD limit (int)
SES_MIN_COURSE = 1

# Maximum courses per session for scheduling. Treated as HARD limit (int)
SES_MAX_COURSE = 4

# Whether or not to allow scheduling outside GI Bill benefits (if GI Bill present). (bool)
EXCEED_BENEFITS = True

# How many sessions to spread the course-load between. Optional. (int | None)
SPREAD_BETWEEN = 15


"""--------------------------------- END User Input -----------------------------------------"""


# Create GIB
if not YEARLY_GIB_AMOUNT:
    gib = None
else:
    gib = ser.create_gib(
        yearly_amount=YEARLY_GIB_AMOUNT,
        start_dt=BENEFIT_YEAR_START,
        remaining_time=BENEFITS_REMAINING,
        days_as_of=BENEFITS_ASOF
    )

# Get Courses
courses = ser.get_courses_pipeline(
    course_path=INPUT_PATH,
    course_path_abs=ABSOLOUTE_PATH,
    in_person= INPERSON_COURSES

)

# Create User
user = ser.create_new_user(
    first_ses_dt=FIRST_SESSION_DATE,
    user_id= USER_ID,
    courses=courses,
    grant_amnt_per_ses= TOTAL_GRANT_AMOUNT_PER_SESSION,
    gib=gib
)

# Create Restraints
restraints = ser.generate_restraints(
    inperson_courses=INPERSON_COURSES,
    in_person_end_dt=INPERSON_END_DT,
    min_inperson=1,
    max_inperson=1,
    ses_max_cost=0.0,
    ses_min_class=2,
    ses_max_class=4,
    exceed_benefits=True
)

# Schedule User's Courses (Operates on User In-Place)
ser.generate_schedule(
    user=user,
    restraints=restraints,
    spread_between=SPREAD_BETWEEN
)

# Export and save User's Schedule
ser.export_schedule(
    user=user,
    format=OUTPUT_TYPE,
    path=OUTPUT_PATH,
    absoloute=OUTPUT_ABS
)
