
"""------------Sorting-----------"""
IN_PERSON_PRIORITY = 5          # Base amount to raise priority of in person classes
CAPSTONE_PRIORITY = 5           # Base amount to LOWER priority of capstone class

"""---------Current Course/Session Costs----------"""
# Costs are now DATED and live in a CSV (one row per price tier; columns:
# Begin Date, Cost Per Session, Cost Per Course, Cost Per CH Undergrad,
# Cost Per CH Grad, Alumni Savings Percent). The tier in effect for a session
# is the latest row whose Begin Date is on/before that session's start date.
# To change prices, add a new row -- existing rows keep historical pricing.
# See src/scheduling/pricing.py.
PRICING_PATH = "config/pricing.csv"
PRICING_PATH_ABS = False        # Bool: is PRICING_PATH absolute?

# Bool trigger to apply alumni savings to grad courses. The savings *percentage*
# itself is dated in the pricing CSV (per tier); this just switches it on/off.
APPLY_ALUMNI_SAVINGS = True
# IF DEV:
# APPLY belongs in restraints, not settings.
# I'm just too lazy to move it at this point.
# Only utilized in 'Course.cost_on()'


"""----------Sessions ------------"""

"""NOTE: Start all sessions on "IDEAL" month, not actual. Holidays will be auto-factored 
and rounded to nearest SESSION_START_DAY.

It is possible for this to be slightly off from actual schedule, resulting in slightly
mis-calculated GIB benefit usage. This is known, understood and disregarded. Assuming
all sessions attempt to start on the first of the month, and start on nearest 
SESSIONS_START_DAY, any difference will be extremely minimal.

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

SESSION_WEEKS = 8               # Length of sessions (as weeks); int only
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

