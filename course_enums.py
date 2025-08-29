from enum import IntEnum

class LevelENUM(IntEnum):
    UNDERGRAD = 0
    GRADUATE = 1

class StatusENUM(IntEnum):
    NONE = 0
    IN_PROGRESS = 1
    COMPLETED = 2

class CourseFilterENUM(IntEnum):
    FREE = 0
    SET_SESSION = 1
    INTENT = 2
    CAPSTONE = 3
