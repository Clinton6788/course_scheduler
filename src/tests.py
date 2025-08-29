from src.intake import get_excel
from src.intake import (
    create_courses,
    organize_courses,
    prioritize_courses
)

# For now, just seeing if any errors raise
def run_tests():
    courses = organize_courses(create_courses(get_excel()))
    l = {}
    for k, v in courses.items():
        l[k] = prioritize_courses(v)
        
    print(l)