from src.user import User, GIB
from src.scheduling import Scheduler, Restraints, Course, Session
from typing import Any, Optional
import datetime as dt
from src.scheduling import Course
from shortuuid import ShortUUID



def create_new_user(
    first_ses_dt: Optional[dt.date] = None,
    user_id: Optional[Any] = None,
    courses: Optional[list[Course]] = None,
    grant_amnt_per_ses: Optional[int | float] = 0,
    gib: Optional[GIB] = None
) -> User:
    """
    Creates and returns a fully initialized User instance with optional courses, grants, and GI Bill benefits.
    All validation is handled here before constructing the User object.

    Args:
        first_ses_dt (datetime.date, optional): Start date of the user's first session.
        user_id (Any, optional): Unique identifier for the user.
        courses (list[Course], optional): All Course objects available to the user.
        grant_amnt_per_ses (int | float, optional): Dollar amount of grant funding per session.
        gib (GIB, optional): GI Bill tracking object.

    Returns:
        User: A fully validated and constructed User instance.

    Raises:
        TypeError, ValueError: For invalid input types or values.
    """
    # Validation
    if first_ses_dt is not None:
        if not isinstance(first_ses_dt, dt.date):
            raise TypeError("first_ses_dt must be a datetime.date instance.")

    if courses is not None and not isinstance(courses, list):
        raise TypeError("courses must be a list of Course instances or None.")
    if courses and not all(isinstance(c, Course) for c in courses):
        raise TypeError("All items in courses must be instances of Course.")

    if grant_amnt_per_ses is not None and not isinstance(grant_amnt_per_ses, (int, float)):
        raise TypeError("grant_amnt_per_ses must be an int or float.")
    if grant_amnt_per_ses and grant_amnt_per_ses < 0:
        raise ValueError("grant_amnt_per_ses cannot be negative.")

    update_gib = False
    if gib is not None:
        if not isinstance(gib, GIB):
            raise TypeError("gib must be an instance of GIB or None.")
        if first_ses_dt is not None:
            update_gib = True

    # Defaults
    if courses is None:
        courses = []
    if user_id is None:
        user_id = ShortUUID.uuid()

    # Construct User, ensure GIB update
    return User(
        user_id=user_id,
        first_ses_dt=first_ses_dt,
        all_courses=courses,
        course_schedule=[],
        grants_per_ses=grant_amnt_per_ses,
        gib=gib
    )

def modify_user(
    user: User,
    first_ses_dt: Optional[dt.date] = None,
    courses: Optional[list[Course]] = None,
    course_schedule: Optional[list[Session]] = None,
    grant_amnt_per_ses: Optional[int | float] = None,
    gib: Optional[GIB] = None
) -> None:
    """
    Modifies an existing User instance with optional updates to core fields.
    All inputs are validated before applying.

    Args:
        user (User): The User instance to modify.
        first_ses_dt (datetime.date, optional): New first session date.
        courses (list[Course], optional): New list of Course instances.
        course_schedule (list[Session], optional): New list of Session instances.
        grant_amnt_per_ses (int | float, optional): Updated grant amount per session.
        gib (GIB, optional): New GI Bill benefit tracking instance.

    Raises:
        TypeError, ValueError: On invalid inputs.
    """
    from src.scheduling import Session
    update_courses = False
    new_gib = False

    if first_ses_dt is not None:
        if not isinstance(first_ses_dt, dt.date):
            raise TypeError("first_ses_dt must be a datetime.date instance.")
        if first_ses_dt < dt.date.today():
            raise ValueError("first_ses_dt cannot be in the past.")
        user.first_ses_dt = first_ses_dt

    if courses is not None:
        if not isinstance(courses, list):
            raise TypeError("courses must be a list of Course instances.")
        if not all(isinstance(c, Course) for c in courses):
            raise TypeError("All items in courses must be instances of Course.")
        user.courses = courses
        update_courses = True

    if course_schedule is not None:
        if not isinstance(course_schedule, list):
            raise TypeError("course_schedule must be a list of Session instances.")
        if not all(isinstance(s, Session) for s in course_schedule):
            raise TypeError("All items in course_schedule must be instances of Session.")
        user.schedule = course_schedule
        update_courses = True

    if grant_amnt_per_ses is not None:
        if not isinstance(grant_amnt_per_ses, (int, float)):
            raise TypeError("grant_amnt_per_ses must be an int or float.")
        if grant_amnt_per_ses < 0:
            raise ValueError("grant_amnt_per_ses cannot be negative.")
        user.grants = grant_amnt_per_ses

    if gib is not None:
        if not isinstance(gib, GIB):
            raise TypeError("gib must be an instance of GIB.")
        user.gib = gib
        new_gib = True

    if update_courses:
        if user.gib and new_gib is False:
            raise ValueError("Must update GIB if courses updated.")
        Scheduler.schedule_set(user)
        if new_gib:
            user.gib.charge_historical(user.completed_sessions)
    
def create_gib(
    yearly_amount: int | float,
    start_dt: tuple[int, int],
    remaining_time: tuple[int, int],
    days_as_of: dt.date
) -> GIB:
    """
    Factory function to create a GIB instance with validation.

    Args:
        yearly_amount (int | float): Yearly financial coverage for the GI Bill.
        start_dt (tuple[int, int]): Tuple (month, day) representing the start 
            date of the benefit year. Month must be 1-12, day must be 1-31.
        remaining_time (tuple[int, int]): Tuple (months, days) representing 
            remaining benefit time. Months and days must be non-negative.
        days_as_of (datetime.date): Date the remaining time was calculated from.

    Returns:
        GIB: An initialized GIB instance ready for tracking user benefits.

    Raises:
        ValueError: If any input is invalid (e.g., month/day out of range, 
            negative remaining time, days_as_of not a date).
    """
    # Validation
    if not isinstance(yearly_amount, (int, float)) or yearly_amount < 0:
        raise ValueError(f"yearly_amount must be non-negative int or float, got {yearly_amount}")

    if not (isinstance(start_dt, tuple) and len(start_dt) == 2):
        raise ValueError("start_dt must be a tuple of (month, day)")

    month, day = start_dt
    if not (1 <= month <= 12):
        raise ValueError(f"start month must be 1-12, got {month}")
    if not (1 <= day <= 31):
        raise ValueError(f"start day must be 1-31, got {day}")

    if not (isinstance(remaining_time, tuple) and len(remaining_time) == 2):
        raise ValueError("remaining_time must be a tuple of (months, days)")
    months, days = remaining_time
    if months < 0 or days < 0:
        raise ValueError(f"remaining_time values must be non-negative, got {remaining_time}")

    if not isinstance(days_as_of, dt.date):
        raise ValueError(f"days_as_of must be a datetime.date, got {type(days_as_of)}")

    # Instantiate GIB
    return GIB(
        yearly_amount=yearly_amount,
        start_dt=start_dt,
        remaining_time=remaining_time,
        days_as_of=days_as_of
    )    
