from src.intake import get_courses_pipeline
from src.scheduler import Scheduler

# Optional, Manual list for now
MUST_HAVE_IN_PERSON = False
IN_PERSON = [] 

def run_main():
    course_dict = get_courses_pipeline(IN_PERSON)
    s = Scheduler()
    s.schedule_courses(courses=course_dict, in_person=IN_PERSON,must_have_inperson=MUST_HAVE_IN_PERSON)

if __name__ == '__main__':
    run_main()