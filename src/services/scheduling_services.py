from src.user import User
from src.scheduling import Restraints, Scheduler as Sch, Session, Course
from typing import Optional
import datetime as dt

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

    # Schedule Set courses
    Sch.schedule_set(user)

    # Schedule Session Levels
    Sch.plan_session_levels(user, restraints, spread_between)

    # Update GI Bill before generating sessions
    if hasattr(user, "gib") and user.gib:
        completed = [s for s in user.schedule if s.start_date <= dt.date.today()]
        user.gib.charge_historical(completed)

    # Schedule Free courses or Raise (inside scheduler)
    Sch.schedule_free(user, restraints, spread_between)



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


def export_schedule(user: User, format: str = "csv"):
    pass

