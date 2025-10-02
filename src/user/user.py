import datetime as dt
from.gib import GIB
from typing import Optional

class User:
    import src.scheduling as sch

    def __init__(
        self,
        user_id,
        first_ses_dt: Optional[dt.date] = None,
        all_courses: Optional[list[sch.Course]] = None,
        course_schedule: Optional[list[sch.Session]] = None,
        grants_per_ses: int | float = 0,
        gib: Optional[GIB] = None,
    ):
        """
        A lightweight container class for course scheduling and benefit tracking.
        All validation is expected to be performed prior to instantiation.
        """
        self.id_ = user_id
        self.first_ses_dt = first_ses_dt
        self.courses = all_courses or []
        self.schedule = course_schedule or []
        self.grants = grants_per_ses
        self.gib = gib

        self.is_scheduled = False
        self.free_sessions = []
        self.assigned_courses = []
        self.completed_sessions = []




