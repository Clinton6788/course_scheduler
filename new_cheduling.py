from src.user import User, GIB
from src.scheduling import Session, Restraints, Course
from config.settings import MAX_RECURSION
import copy

def get_user_sessions(user: User, rest: Restraints) -> None:
    pass

def get_tgt_list(user: User, rest: Restraints) -> list[int]:
    pass

def schedule_user(user: User, rest: Restraints, tgt_list: list) -> tuple[bool,list]:
    pass

def schedule_pipeline(
        user: User,
        rest: Restraints,
) -> User:
    """Main entry and pipeline for scheduling user courses. Attempts to schedule
    all user courses based on restraints.

    Args:
        user (User): User to schedule. All courses should be present in attr 'courses'.
        rest (Restraints): Restraints obj configured for this schedule attempt.

    Raises:

    Returns:
        user (User): User, with all scheduled sessions. NOTE: Returned user object is 
        a COPY of the original. Return obj must be caught and will replace original
        user object.
    """
    # Assign all session objects to User
    get_user_sessions(user, rest)

    # Get target list based on available sessions and restraints
    # Target list used to determine how many courses/session
    tgt_list = get_tgt_list(user, rest)

    # Recursive Scheduling ------------------------

    # Recursion counter
    recur = 0
    # Success flag
    suc = False
    
    # Recursively call 
    while suc is False and recur <= MAX_RECURSION:
        # Create copy of user for modification
        usr_cpy = copy.deepcopy(user)

        # Attempt scheduling
        suc, tgt_list = schedule_user(usr_cpy, rest, tgt_list)

    # Handle success
    if suc:
        # New user is to be returned
        return usr_cpy
    
    # Handle failure:
    if recur > MAX_RECURSION:
        raise RecursionError("Scheduling Failed: Max recursion hit!")
    else:
        raise RuntimeError("Unknown Error Occured in Schedule Pipeline!")