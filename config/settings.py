from datetime import date

"""------------Defaults------------"""
# ALL displayed here are DEFAULTS only (For rapid/set configs).

# Path for course spreadsheet. 
# Accepts Filetypes: csv, xls, xlsx
COURSES_PATH = "course_input.csv"
ABSOLOUTE_PATH = False              # Bool, Is path absoloute; False for relative

class RestraintsENUM():
    # Session Restraints
    SES_MIN_INPERSON = 0
    SES_COST_COVERED = 1    
    SES_MAX_CLASS = 2    
    SES_MIN_CLASS = 3
    SES_MONTHS = 4
    SES_MAX_COST = 5
    SES_MAX_CH = 6
    SES_MIN_CH = 7
    SES_FIRST_ONLY_INPERSON = 8



"""------------Config-----------"""
IN_PERSON_PRIORITY = 10         # Base amount to raise priority of in person classes

"""---------Current Course Costs----------"""
COST_PER_SESSION = 40
COST_PER_COURSE = 100           # Additional costs only (outside of cost/ch)
COST_PER_CH_UNDERGRAD = 514
COST_PER_CH_GRAD = 776
ALUMNI_SAVINGS_PERCENT = 20     # Whole percentage; Ex: '20' for 20%.... NOT 0.2.... **ONLY APPLIES TO GRAD LEVEL**


"""----------Sessions ------------"""

"""NOTE: Start all sessions on "IDEAL" month, not actual. Holidays will be auto-factored 
and rounded to nearest SESSION_START_DAY.

It is possible for this to be slightly off from actual schedule, resulting in slightly
mis-calculated GIB benefit usage. This is known, understood and disregarded.

Current, hard-coded max deviation is +- 1 week from target start date. If holidays prevent
this from happening, holidays will be ignored and closest date will be applied.
"""

# INT list of months which start new session (ACTUAL int: 6 for june, etc.)
SESSION_MONTHS = [
    1,
    3,
    5,
    7,
    9,
    11,
]

SESSION_WEEKS = 8              # Length of sessions (as weeks); int only
SESSION_START_DAY = 6           # INT representation of weekday. Monday = 0

# List of holidays to be ignored (If start date falls on holiday weekend)
# NOTE: Recommend commenting out unused rather than deleting, for future reference.
SESSION_HOLIDAYS = [
    "new_year",
    "mlk_day",
    "presidents_day",
    "memorial_day",
    "juneteenth",
    "independence_day",
    "labor_day",
    "columbus_day",
    "veterans_day",
    "thanksgiving",
    "christmas",
]

