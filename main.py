from src.intake import get_courses_pipeline
from src.scheduler import Scheduler
from course_enums import RestraintsENUM as R


RESTRAINTS = {
    R.FIRST_SES_INPERSON: False,    # Bool, Does first session need to be in person
    R.SES_COST_COVERED: False,      # Bool, Does the session need to be completely covered financially
    R.SES_MAX_CLASS: 4,             # Int, Max number of classes per session
}

# Optional IF 'R.FIRST_SES_INPERSON' = False, else mandatory
IN_PERSON = [] 


import pickle
from pathlib import Path
from src.intake import get_courses_pipeline

def store_data():
    course_dict = get_courses_pipeline([])

    file_path = Path.cwd() / "course_dict.pkl"
    with open(file_path, "wb") as f:
        pickle.dump(course_dict, f)

def load_data():
    file_path = Path.cwd() / "course_dict.pkl"

    # To load back:
    with open(file_path, "rb") as f:
        loaded_courses = pickle.load(f)
    return loaded_courses



def run_main():
    course_dict = load_data()
    # course_dict = get_courses_pipeline(IN_PERSON)

    print(course_dict)
    s = Scheduler()
    s.schedule_courses(courses=course_dict, restraints=RESTRAINTS, inperson=IN_PERSON)
    for _, ses in s.sessions.items():
        print(f"Session {ses}")

if __name__ == '__main__':
    run_main()