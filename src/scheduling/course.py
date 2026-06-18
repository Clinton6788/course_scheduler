from dataclasses import dataclass
from typing import List, Optional
import datetime as dt
from config.settings import APPLY_ALUMNI_SAVINGS
from config.course_enums import LevelENUM
from src.scheduling.pricing import get_pricing
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
        transfer_intent (bool, optional): True if intend to take via Sophia.
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
    transfer_intent: bool = False
    challenge_intent: bool = False
    priority: int = 0

    def __post_init__(self):
        # Fail fast on an invalid level (cost is now computed per-date in cost_on()).
        if self.level not in (LevelENUM.GRADUATE, LevelENUM.UNDERGRAD):
            raise ValueError(f"{self.course_id=}||Improper {self.level=}")

    def cost_on(self, date: dt.date) -> float:
        """Cost of this course under the price tier in effect on ``date``.

        ``date`` is the start date of the session the course is being scheduled
        into, so the same course can cost different amounts in different sessions
        if a price change falls between them.
        """
        tier = get_pricing(date)
        p = 1
        if self.level == LevelENUM.GRADUATE:
            m = tier.cost_per_ch_grad
            if APPLY_ALUMNI_SAVINGS:
                p = (100 - tier.alumni_savings_percent) / 100
        elif self.level == LevelENUM.UNDERGRAD:
            m = tier.cost_per_ch_undergrad
        else:
            raise ValueError(f"{self.course_id=}||Improper {self.level=}")

        gross = self.credit_hours * m + tier.cost_per_course
        return round(gross * p, 2)

    def __repr__(self):
            return (f"Course(course_id='{self.course_id}', level={self.level}, status={self.status}, "
                    f"session={self.session}, priority={self.priority})")


    def __eq__(self, other):
        if isinstance(other, Course):
            return self.course_id == other.course_id
        else:
            return self.course_id == other

    def __lt__(self, other):
        if isinstance(other, Course):
            return self.priority < other.priority
        else:
            return self.priority < other