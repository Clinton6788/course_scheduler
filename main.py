from src.intake import get_courses_pipeline

# Optional, Manual list for now
IN_PERSON = [] 

def run_main():
    course_dict = get_courses_pipeline(IN_PERSON)


if __name__ == '__main__':
    run_main()