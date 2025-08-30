from src.intake import get_courses_pipeline
from src.scheduler import Scheduler
from src.course_enums import RestraintsENUM as R





FILE_PATH = "/mnt/c/Users/clint/OneDrive/Documents/Education/DeVry/A-Scheduling/import_for_py.xlsx"
ABSOLOUTE_PATH = True

RESTRAINTS = {
    R.FIRST_SES_INPERSON: False,    # Bool, Does first session need to be in person
    R.SES_COST_COVERED: False,      # Bool, Does the session need to be completely covered financially
    R.SES_MAX_CLASS: 4,             # Int, Max number of classes per session
}

"""IN_PERSON:
Optional IF 'R.FIRST_SES_INPERSON' = False, else mandatory
Can be:
    List, 
    Str("path/to/inperson/excel"),
    None
"""
IN_PERSON = [] 





def get_schedule():

    course_dict = get_courses_pipeline(FILE_PATH, ABSOLOUTE_PATH, IN_PERSON)

    s = Scheduler()
    s.schedule_courses(courses=course_dict, restraints=RESTRAINTS, inperson=IN_PERSON)
    for _, ses in s.sessions.items():
        print(f"Session {ses}")










if __name__ == '__main__':
    get_schedule()