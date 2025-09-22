from src.intake import get_courses_pipeline
from src.scheduler import Scheduler
from config.course_enums import RestraintsENUM as R
from config.settings import (
    COURSES_PATH,
    ABSOLOUTE_PATH,
    RESTRAINTS
)





"""IN_PERSON:
Optional IF 'R.FIRST_SES_INPERSON' = False, else mandatory
Must be list of course IDs, or empty list
"""
IN_PERSON = [] 





def get_schedule():

    course_dict = get_courses_pipeline(COURSES_PATH, ABSOLOUTE_PATH, IN_PERSON)

    s = Scheduler()
    s.schedule_courses(courses=course_dict, restraints=RESTRAINTS, inperson=IN_PERSON)
    for _, ses in s.sessions.items():
        print(f"Session {ses}")










if __name__ == '__main__':
    get_schedule()