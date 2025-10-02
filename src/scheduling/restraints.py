from typing import Optional
import datetime as dt

class Restraints:
    """
    Defines scheduling constraints for course planning.

    Attributes:
    - inperson_courses (list[str], optional): List of available in-person course names.
    - min_inperson (int, optional): Minimum required in-person sessions (hard limit).
    - max_inperson (int, optional): Maximum allowed in-person sessions (soft limit).
    - in_person_end_dt (dt.date, optional): Last date on which in-person sessions are allowed.
    - ses_max_cost (int | float, optional): Maximum cost after deductions allowed per session.
    - ses_min_class (int, optional): Minimum number of classes per session. Default is 2.
    - ses_max_class (int, optional): Maximum number of classes per session. Default is 4.
    - exceed_benefits (bool, optional): Allows scheduling of sessions beyond GIB benefits. Default is False.
    """
    def __init__(
        self,
        inperson_courses: Optional[list[str]] = None,
        min_inperson: Optional[int] = None,
        max_inperson: Optional[int] = None,
        in_person_end_dt: Optional[dt.date] = None,
        ses_max_cost: Optional[int | float] = None,
        ses_min_class: int = 2,
        ses_max_class: int = 4,
        exceed_benefits: bool = False
    ):
        self.inperson_courses = inperson_courses
        self.min_inperson = min_inperson
        self.max_inperson = max_inperson
        self.in_person_end_dt = in_person_end_dt
        self.ses_max_cost = ses_max_cost
        self.ses_min_class = ses_min_class
        self.ses_max_class = ses_max_class
        self.exceed_benefits = exceed_benefits