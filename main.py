from src.scheduling import Scheduler
from src.user import User, GIB
from src.intake import get_courses_pipeline
import datetime as dt

COURSES_PATH = "course_input.csv"
ABSOLOUTE_PATH = False              # Bool, Is path absoloute; False for relative
USER_FIRST_SES_DT = dt.date(2025,5,1)
TOTAL_GRANTS_PER_SES = 2099

# GI Bill
GI_BILL_YEARLY = 27120                  # YEARLY Amount of Coverage
GI_BILL_START = (8, 1)                  # Month, Day
BENEFITS_TIME = (23, 10)                # Months, Days of Benefits Remaining
BENEFITS_ASOF = dt.date(2025, 8, 27)    # Date BENEFITS_TIME updated

courses = get_courses_pipeline(COURSES_PATH,ABSOLOUTE_PATH)

print(len(courses))

gibill = GIB(yearly_amount=GI_BILL_YEARLY,
            start_dt=GI_BILL_START,
            remaining_time=BENEFITS_TIME,
            days_as_of=BENEFITS_ASOF
            )

user = User("usr1", 
            USER_FIRST_SES_DT, 
            courses,
            grants_per_ses=TOTAL_GRANTS_PER_SES,
            gib=gibill)

Scheduler.







# if __name__ == '__main__':
#     for i in range (5):
#         print(i+1)