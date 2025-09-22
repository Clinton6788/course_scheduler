from datetime import date
from config.course_enums import RestraintsENUM as R

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
SESSIONS_PER_SEMESTER = 2
SEMESTERS_PER_YEAR = 3


"""---------Current Course Costs----------"""
COST_PER_SESSION = 40
COST_PER_COURSE = 100           # Additional costs only (outside of cost/ch)
COST_PER_CH_UNDERGRAD = 514
COST_PER_CH_GRAD = 776
ALUMNI_SAVINGS_PERCENT = 20     # Whole percentage; Ex: '20' for 20%.... NOT 0.2.... **ONLY APPLIES TO GRAD LEVEL**


"""----------Sessions Start Dates------------"""
SESSIONS = {
    1: date(2025, 5, 5),   
    2: date(2025, 7, 7),   
    3: date(2025, 9, 1),   
    4: date(2025, 10, 27), 
    5: date(2026, 1, 5),   
    6: date(2026, 3, 2),   
    7: date(2026, 5, 4),   
    8: date(2026, 7, 6),   
    9: date(2026, 9, 7),   
    10: date(2026, 11, 2), 
    11: date(2027, 1, 4),  
    12: date(2027, 3, 1),  
    13: date(2027, 5, 3),  
    14: date(2027, 7, 5),  
}

"""-----------Financial Aid--------------"""
# Grants are PER SESSION
GRANT_PELL = 1849
GRANT_OPP = 250

# GI Bill
GI_BILL = 27120 # YEARLY Amount of Coverage
GI_BILL_START = (8, 1) # Month, Day
GI_BILL_END = (7, 31) # Month, Day

BENEFITS_TIME = (23, 10) # Months, Days of Benefits Remaining
BENEFITS_ASOF = date(2025, 8, 27) # Date BENEFITS_TIME updated