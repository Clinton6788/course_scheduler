from src.user import User
from src.scheduling import Restraints, Scheduler as Sch, Session, Course
from typing import Optional
import datetime as dt
import csv
import os

def generate_schedule(
    user: User, 
    restraints: Optional[Restraints] = None, 
    spread_between: Optional[int] = None,
    **kwargs) -> None:
    """
    Generates a schedule for a user, using a Restraints object or individual kwargs.
    Schedule is created in-place, under attr User.schedule (session objects).

    Args:
        user: User object to schedule.
        restraints (Optional[Restraints]): Prebuilt Restraints object.
        spread_between (int): If an int is passed, sprease courses between <int> sessions.
            Default is None (Will not spread).
        **kwargs: Optional fields to create a Restraints object if none provided.
    """
    print(f"Generating schedule for user {user.id_}")
    # Build restraints if not provided
    if restraints is None:
        restraints = generate_restraints(**kwargs)

    # Create sessions
    Sch.create_all_sessions(user, restraints)

    print(f"User Sessions: {user.schedule}|||{user.free_sessions}")

    # Schedule Set courses
    Sch.schedule_set(user)

    # Schedule Session Levels
    # Sch._plan_session_levels(user, restraints, spread_between)

    # Update GI Bill before generating sessions
    if hasattr(user, "gib") and user.gib:
        completed = [s for s in user.schedule if s.start_date <= dt.date.today()]
        user.gib.charge_historical(completed)

    # Schedule Free courses or Raise (inside scheduler)
    Sch.schedule_free(user, restraints)


def generate_restraints(**kwargs) -> Restraints:
    """
    Generate a Restraints object from provided keyword arguments.

    Args:
        **kwargs: Any fields for Restraints, e.g.
            inperson_courses, min_inperson, ses_max_class, etc.

    Returns:
        Restraints: Validated restraints object.

    Raises:
        ValueError: If any field has an invalid type.
    """
    allowed_fields = {
        "inperson_courses", "min_inperson", "max_inperson", "in_person_end_dt",
        "ses_max_cost", "ses_min_class", "ses_max_class", "exceed_benefits"
    }

    # Validate kwargs
    for key in kwargs:
        if key not in allowed_fields:
            raise ValueError(f"Invalid Restraints field: {key}")

    return Restraints(**kwargs)

def export_schedule(
    user: User, 
    format: str = "csv", 
    path: str = "schedule.csv",
    absoloute: bool = False
):
    if format != "csv":
        raise ValueError(f"Unsupported format: {format}")

    # Convert to absolute path if necessary
    output_path = os.path.abspath(path) if absoloute else path

    user.schedule.sort()

    with open(output_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Session", "Start Date", "Courses", "Intent Courses", "Total CH", "Total Cost", "User Cost"])

        for session in user.schedule:
            session_num = session.num
            course_ids = ', '.join(course.course_id for course in session.courses)
            intent_ids = ', '.join(course.course_id for course in session.intent)
            start_date = session.start_date.isoformat() if hasattr(session.start_date, 'isoformat') else session.start_date
            total_ch = session.tot_ch
            total_cost = session.tot_cost
            user_cost = session.adj_cost

            writer.writerow([session_num, start_date, course_ids, intent_ids, total_ch, total_cost, user_cost])