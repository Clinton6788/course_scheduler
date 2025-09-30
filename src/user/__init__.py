from config.course_enums import LevelENUM as L
from .restraints import Restraints
import datetime as dt
from.gib import GIB

class User:
    import src.scheduling as sch
    def __init__(
        self,
        user_id,
        first_ses_dt: dt.date,
        all_courses: list[sch.Course] = [],
        course_schedule: list[sch.Session] = [],
        grants_per_ses: int | float = None,
        gib: GIB = None,
    ):
        """
        Initialize a User instance for course scheduling and benefit tracking.

        Args:
            user_id (Any): Unique identifier for the user.

            first_ses_dt (datetime.date): Start date of the user's first session.
                MUST be accurate year, month in accordance with defined session 
                months. Day should be set to 1.

            all_courses (list[Course], optional): Flat list of all Course objects
                available to the user.

            course_schedule (list[Session], optional): List of Session objects 
                the user is scheduled for. (For DB Integration)

            grants_per_ses (int | float, optional): Dollar amount of grant 
                available per session.

            gib (GIB, optional): GI Bill or similar educational benefit information.

        """
        # Assign attrs
        self.id_ = user_id
        self.first_ses_dt = first_ses_dt
        self.courses = all_courses
        self.schedule = course_schedule
        self.grants = grants_per_ses
        self.gib = gib

        # Default inits
        self.is_scheduled = False
        self.free_sessions = []
        self.assigned_courses = []


        # Create sessions, assign completed or set courses to sessions.
        self._assign_set()


        
    def _assign_set(self):
        for c in self.courses:
            # Break early if course not set
            if c.session is None:
                continue

            # Create Session obj if not exists
            if not c.session in self.schedule:
                self._create_session(c.session)



    def get_schedule(self):
        pass

    def _create_session(self, ses_num):
        """Initializes Session objects based on first session date and SESSIONS
        configure in settings.
        """



    def _schedule_set(self):
        """Assign any courses with set sessions."""
        for c in self.free_courses:
            # Break early if not assigned
            if c.session is None:
                continue

            # Assign to designated session

