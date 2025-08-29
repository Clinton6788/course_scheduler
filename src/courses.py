from dataclasses import dataclass, field
from typing import List, Optional
from settings import (
    COST_PER_CH_GRAD,
    COST_PER_CH_UNDERGRAD,
    COST_PER_COURSE,
    ALUMNI_SAVINGS_PERCENT
)
from course_enums import LevelENUM
from functools import total_ordering

@total_ordering
@dataclass
class Course:
    """
    Represents a course in the scheduling system.

    Attributes:
        course_id (str): Unique course identifier.
        credit_hours (int): Credit hours for the course.
        status (int): Current course status (StatusENUM).
        level (int): Course level (LevelENUM).
        pre_reqs (List, optional): Prerequisites list, nested ['required', ['this','OR','this']].
        dependent_count (int, optional): Number of courses dependent on this as pre-req
        capstone (bool, optional): True if the course must be in the last session for its level.
        session (Optional[int], optional): Assigned session number. Required if status is Completed or InProgress.
        sophia_avail (bool, optional): True if available via Sophia.
        sophia_intent (bool, optional): True if intend to take via Sophia.
        challenge_avail (bool, optional): True if available via challenge exam.
        challenge_intent (bool, optional): True if intend to take via challenge exam.
    """
    course_id: str
    credit_hours: int
    status: int  # ENUM StatusENUM
    level: int  # ENUM LevelENUM
    pre_reqs: str
    dependent_count: int = 0
    capstone: bool = False
    session: Optional[int] = None
    sophia_avail: bool = False
    sophia_intent: bool = False
    challenge_avail: bool = False
    challenge_intent: bool = False
    priority: int = 0
    cost: float = field(init=False)

    def __post_init__(self):
        if self.level == LevelENUM.GRADUATE:
            m = COST_PER_CH_GRAD
            p = (100-ALUMNI_SAVINGS_PERCENT)/100
        elif self.level ==LevelENUM.UNDERGRAD:
            m = COST_PER_CH_UNDERGRAD
            p = 1
        else:
            raise ValueError(f"{self.course_id=}||Improper {self.level=}")
        
        gross = self.credit_hours * m + COST_PER_COURSE
        self.cost = round(gross * p, 2)

    def __eq__(self, other):
        if isinstance(other, Course):
            return self.course_id == other.course_id
        else:
            return self.course_id == other

    def __lt__(self, other):
        return self.priority < other.priority