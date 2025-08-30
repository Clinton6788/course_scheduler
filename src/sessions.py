from settings import (
    SESSIONS,
    COST_PER_SESSION,
)
from datetime import timedelta
from course_enums import LevelENUM
from src.courses import Course

"""DOWN AND DIRTY; Don't Perfect!"""

class Session:
    """Represents one session. Outside of init, all changes must be made through Session.modify()."""
    def __init__(self, session_num: int):
        # Define for easy location
        self._num = session_num
        self.level = None
        self._courses = []
        self._intent = [] # 'Free' classes intend to be completed outside college

        self._start_date = None
        self._end_date = None

        self._tot_courses = 0
        self._tot_ch = 0
        self._tot_cost = 0
        self.adj_cost = 0

        self._pre_reqs = []

        # Calc Values
        self._calc_dates()

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

    def _calc_dates(self):
        self._start_date = SESSIONS.get(self.num)
        self._end_date = self.start_date + timedelta(weeks=8)

    def _calc_courses(self):
        self._tot_cost = COST_PER_SESSION
        for c in self._courses:
            # Validate level
            assert self.level == c.level, f"Session||Level Difference||{self.level=}||{c.level=}"
            self._tot_courses += 1
            self._tot_ch += c.credit_hours
            self._pre_reqs.append(c.pre_reqs)
            self._tot_cost += c.cost

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
            
        
        
        
    




