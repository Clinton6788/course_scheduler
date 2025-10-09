from config.settings import (
    COST_PER_SESSION,
    SESSION_START_DAY,
    SESSION_WEEKS
)
import datetime as dt
from config.course_enums import LevelENUM
from src.scheduling.course import Course
from src.helpers import round_to_nearest_weekday_start

"""DOWN AND DIRTY; Don't Perfect!"""

class Session:
    """Represents one session. Outside of init, all changes must be made through Session.modify()."""
    def __init__(self, session_num: int, start_date: dt.date, target_month: int):
        # Define for easy location
        self._num = session_num
        self.level = None
        self._courses = []
        self._intent = []       # Courses intended to be completed outside sessions (challenge, transfer)
        self._grants_applied = 0
        self._gib_applied = 0
        self.gib_remaining = 0

        self._start_date = round_to_nearest_weekday_start(
                                start_date, 
                                target_month,
                                SESSION_START_DAY,
                                )
        self._end_date = self._start_date + dt.timedelta(weeks=SESSION_WEEKS)
        self._month = target_month

        self._tot_courses = 0
        self._tot_ch = 0
        self._tot_cost = 0
        self._adj_cost = 0

        self._pre_reqs = []


    # region Comp Dunders
    def __repr__(self):
        course_ids = [c.course_id for c in self._courses]
        return f"Session {self._num}: {course_ids}"
    

    def _get_comp_val(self, other):
        if isinstance(other, Session):
            return other._num
        return int(other)

    def __eq__(self, other):
        return self._num == self._get_comp_val(other)

    def __lt__(self, other):
        return self._num < self._get_comp_val(other)

    def __le__(self, other):
        return self._num <= self._get_comp_val(other)

    def __gt__(self, other):
        return self._num > self._get_comp_val(other)

    def __ge__(self, other):
        return self._num >= self._get_comp_val(other)

    def __ne__(self, other):
        return self._num != self._get_comp_val(other)
    # endregion

    def add_grants(self, total_amount:float | int):
        """Add a grant amount to be subtracted from total value
        """
        assert isinstance(total_amount, (int, float)), f"Grant wrong type: {type(total_amount)}"
        self._grants_applied += total_amount
        self._calc_courses()

    def add_gib(self, total_amount: float | int):
        """Adds an amount of benefit coverage to be subtracted from total value.
        """
        assert isinstance(total_amount, (int, float)), f"GIB Value wrong type: {type(total_amount)}"
        self._gib_applied = total_amount
        self._calc_courses()


    def _calc_courses(self):
        self._tot_cost = COST_PER_SESSION
        self._tot_ch = 0
        self._tot_cost = 0
        self._tot_courses = 0
        self._pre_reqs = []
        
        for c in self._courses:
            # Validate level
            assert self.level == c.level, f"Session||Level Difference||{self.level=}||{c.level=}"
            self._tot_courses += 1
            self._tot_ch += c.credit_hours
            self._pre_reqs.append(c.pre_reqs)
            self._tot_cost += c.cost

        self._adj_cost = self._tot_cost - self._grants_applied - self._gib_applied

        # Ensure more benefits than necessary not being used 
        # (Allow a dollar for wiggle/rounding):
        if self._adj_cost <-1:
            raise ValueError(f"Session ADJ Cost Too Low:\n"
                f"{self._num=}\n{self._adj_cost=}\n{self._grants_applied=}\n"
                f"{self._gib_applied=}")

    def add_course(self, course: Course):
        self._courses.append(course)
        self._calc_courses()

    def drop_course(self, course: Course):
        try:
            self._courses.remove(course)
        except ValueError:
            return
        self._calc_courses()

    def add_intent(self, course: Course):
        self._intent.append(course)

    def drop_intent(self, course: Course):
        try:
            self._intent.remove(course)
        except ValueError:
            return
        

    @property
    def gib_applied(self):
        """Total amount of GI Bill finances applied"""
        return self._gib_applied
    
    @property
    def grants_applied(self):
        """Total amount of grants applied"""
        return self._grants_applied

    @property
    def adj_cost(self):
        """User cost for session"""
        return self._adj_cost

    @property
    def intent(self):
        """List of 'Intent' courses"""
        return self._intent

    @property
    def num(self):
        """Session Number"""
        return self._num

    @property
    def courses(self):
        """List of Course Objects in this session"""
        return self._courses

    @property
    def start_date(self):
        """Session start date"""
        return self._start_date

    @property
    def end_date(self):
        """Session end date"""
        return self._end_date

    @property
    def tot_courses(self):
        """Total number of courses in this session"""
        return self._tot_courses

    @property
    def tot_ch(self):
        """Total credit hours for this session"""
        return self._tot_ch

    @property
    def tot_cost(self):
        """Total cost for this session"""
        return self._tot_cost

    @property
    def pre_reqs(self):
        """List of prerequisites for this session"""
        return self._pre_reqs
            
        
        
        
    




