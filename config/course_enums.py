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

class SessErrENUM(IntEnum):
    NOT_INPERSON = 0
    OVER_MAX_COST = 1
    OUT_OF_BENEFITS = 3
    PREREQ_NOT_MET = 4

class CourseLoadENUM(IntEnum):
    FRONT_HEAVY = 0
    REAR_HEAVY = 1
    PYRAMID = 2
    BALANCED = 3