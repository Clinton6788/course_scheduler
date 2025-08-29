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

class RestraintsENUM(IntEnum):
    # Any changes must be reflected in src.scheduler > Scheduler._is_valid_schedule()
    FIRST_SES_INPERSON = 0 
    SES_COST_COVERED = 1    
    SES_MAX_CLASS = 2       

class SessErrENUM(IntEnum):
    NOT_INPERSON = 0
    COST_NOT_COVERED = 1
    OVER_MAX_CLASS = 2
    OUT_OF_BENEFITS = 3
    PREREQ_NOT_MET = 4