from src.intake import get_courses_pipeline
from src.scheduler import Scheduler
from course_enums import RestraintsENUM as R


RESTRAINTS = {
    R.FIRST_SES_INPERSON: False,    # Bool, Does first session need to be in person
    R.SES_COST_COVERED: False,      # Bool, Does the session need to be completely covered financially
    R.SES_MAX_CLASS: 4,             # Int, Max number of classes per session
    R.GIBILL_SETS_LAST: True        # Bool, Do the GI Bill benefits dictate the last session
}

# Optional IF 'R.FIRST_SES_INPERSON' = False, else mandatory
IN_PERSON = [] 


def run_main():
    course_dict = get_courses_pipeline(IN_PERSON)
    print(course_dict)
    # s = Scheduler()
    # s.schedule_courses(courses=course_dict, restraints=RESTRAINTS, inperson=IN_PERSON)

if __name__ == '__main__':
    run_main()