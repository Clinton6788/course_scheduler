from datetime import date

"""------------Config-----------"""
IN_PERSON_PRIORITY = 20 # Base amount to raise priority of in person classes
SESSIONS_PER_SEMESTER = 2
SEMESTERS_PER_YEAR = 3
MAX_RECURSION = 20

"""---------Current Course Costs----------"""
COST_PER_SESSION = 40
COST_PER_COURSE = 100 # Additional costs only; total
COST_PER_CH_UNDERGRAD = 514
COST_PER_CH_GRAD = 776
ALUMNI_SAVINGS_PERCENT = 20 # Whole percentage; Ex: '20' for 20%.... NOT 0.2.... **ONLY APPLIES TO GRAD LEVEL**


"""----------Sessions Start Dates------------"""
SESSIONS = {
    1: date(2025, 5, 5),   # Completed
    2: date(2025, 7, 7),   # Completed
    3: date(2025, 9, 1),   # Completed
    4: date(2025, 10, 27), # Completed
    5: date(2026, 1, 5),   # Scheduled
    6: date(2026, 3, 2),   # Scheduled
    7: date(2026, 5, 4),   # Placeholder, exact date TBD
    8: date(2026, 7, 6),   # Placeholder, exact date TBD
    9: date(2026, 9, 7),   # Placeholder, exact date TBD
    10: date(2026, 11, 2), # Placeholder, exact date TBD
    11: date(2027, 1, 4),  # Placeholder, exact date TBD
    12: date(2027, 3, 1),  # Placeholder, exact date TBD
    13: date(2027, 5, 3),  # Placeholder, exact date TBD
    14: date(2027, 7, 5),  # Placeholder, exact date TBD
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