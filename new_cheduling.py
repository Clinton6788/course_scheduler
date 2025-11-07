from src.user import User, GIB
from src.scheduling import Session, Restraints, Course
from config.settings import MAX_RECURSION
import copy
from src.scheduling import Scheduler as Sch
from dataclasses import dataclass, field

class Targets:
    def __init__(
            self,
            undergrad: list = [],
            grad: list = [],
            ):
        self._under = undergrad
        self._grad = grad
        self._complete = [*undergrad, *grad]
        self._historical = []

    @property
    def under(self):
        return self._under
    
    @under.setter
    def under(self, value):
        assert isinstance(value, list), f"Must be type list || is {type(value)}"
        assert all(isinstance(x,int) for x in value), f"All elements must be int || {value=}"
        self._under = value
        self._complete = [*self._under, *self._grad]

    @property
    def grad(self):
        return self._grad
    
    @grad.setter
    def grad(self, value):
        assert isinstance(value, list), f"Must be type list || is {type(value)}"
        assert all(isinstance(x,int) for x in value), f"All elements must be int || {value=}"
        self._grad = value
        self._complete = [*self._under, *self._grad]

    @property
    def complete(self):
        return self._complete
    
    def get_historical(self):
        return self._historical
    
    def add_historical(self, value:list):
        assert isinstance(value, list), f"Must be type list || is {type(value)}"
        assert all(isinstance(x,int) for x in value), f"All elements must be int || {value=}"
        self._historical.append(value)

def get_user_sessions(user: User, rest: Restraints) -> None:
    pass

def get_tgt_list(user: User, rest: Restraints) -> list[int]:
    pass

def schedule_user(user: User, rest: Restraints, tgt_list: list) -> tuple[bool,list]:
    # Ensure we attempt to reduce credit hours before failing.
    pass

def schedule_pipeline(
        user: User,
        rest: Restraints,
        spread_between: int = None
) -> User:
    """Main entry and pipeline for scheduling user courses. Attempts to schedule
    all user courses based on restraints. DOES NOT RAISE, only prints on failure.

    Args:
        user (User): User to schedule. All courses should be present in attr 'courses'.
        rest (Restraints): Restraints obj configured for this schedule attempt.
        spread_between (int, optional): Number of sessions to spread courseload between.

    Returns:
        user (User): User, with all scheduled sessions. NOTE: Returned user object is 
        a COPY of the original. Return obj must be caught and will replace original
        user object. If recursion limit hit, object still returned for assessment.
    """
    # Assign all session objects to User
    Sch.create_all_sessions(user, rest, spread_between)

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
        print("Scheduling Failed: Max recursion hit!")
        return usr_cpy
    else:
        raise RuntimeError("Unknown Error Occured in Schedule Pipeline!")