from .course import Course
from .sessions import Session
from config.course_enums import LevelENUM
from src.user import User, Restraints
from src.helpers import round_to_nearest_weekday_start
from config.settings import SESSION_MONTHS
import datetime as dt

class SchedulingError(Exception):
    """Raised when a valid schedule cannot be created given the restraints."""
    pass


class Scheduler:
    """Need to 
    create sessions
    compare to existing sessions, discard any the already exist
    schedule set courses
    schedule by level
        schedule by restraints
    """

    @classmethod
    def create_all_sessions(cls, user: User, restraints: Restraints) -> None:
        """Creates all possible sessions for User instance, based on 
        len(user.courses) and Restraints.ses_min_class.
        
        Args:
            user (User): User instance with all potential Course objects in 
                attr 'user.courses'.
            restraints (Restraints): Restraints instance with all applicable 
                fields.
        """
        print(f"Creating sessions for {user.id_}...")
        r = restraints
        u = user

        # Get total required sessions
        under_count = 0
        grad_count = 0

        # Seperate by level (Hard-coded assumption of no mixing levels throughout)
        for c in u.courses:
            if c.level == LevelENUM.UNDERGRAD:
                under_count += 1
                continue
            if c.level == LevelENUM.GRADUATE:
                grad_count += 1
                continue
            raise ValueError(f"Create Sessions||Course has improper level: {c.level}")
        
        # Get required session counts
        # NOTE: Counts will often be MORE than required which is FINE.
        # Calc undergrad
        under_ses = under_count // r.ses_min_class 
        under_ses += 1 if under_count % r.ses_min_class >= 1 else 0
        # Calc Grad
        grad_ses = grad_count // r.ses_min_class
        grad_ses += 1 if grad_count % r.ses_min_class >= 1 else 0


        # Get dates and create sessions
        # Ensure sorted
        ses_months = SESSION_MONTHS.copy()
        ses_months.sort()

        # Get year, month counters
        yr = u.first_ses_dt.year
        mo_index = ses_months.index(u.first_ses_dt.month)

        # Init Session tracking
        full_sessions = []
        ses_num = 1

        def generate_sessions(level: int, num_ses: int):
            nonlocal ses_num, mo_index, yr

            # Iter and create
            for _ in range(num_ses):
                mo = SESSION_MONTHS[mo_index]
                ses = Session(
                    ses_num, 
                    dt.date(yr,mo,1),
                    mo)
                ses.level = level
                full_sessions.append(ses)

                # Increment
                ses_num += 1
                mo_index += 1
                if mo_index >= len(ses_months):
                    mo_index = 0
                    yr += 1

        # Call for each level. MUST start with undergrad
        generate_sessions(LevelENUM.UNDERGRAD, under_ses)
        generate_sessions(LevelENUM.GRADUATE, grad_ses)

        # Ensure no existing session in user
        for s in full_sessions:
            # Compare by number only
            if s in user.schedule:
                full_sessions.remove(s)

        # Set as free_sessions (Override any existing)
        # Sort to keep lowest available first
        u.free_sessions = full_sessions.sort()

        print("Sessions creation complete.")

    @classmethod
    def schedule_set(cls, user: User) -> None:
        """Schedules all Courses with 'set' session number. This includes 
        statuses: 'complete' and 'inprocess', assuming proper intake format. 
        Modifies 'User' inplace.

        Args:
            user (User): User instance with all potential Course objects in 
                attr 'user.courses'.
        """
        print(f"Scheduling set courses for {user.id_}...")

        # Ensure sorted sessions
        user.free_sessions.sort()

        # Find set courses
        for c in user.courses:
            if not isinstance(c.session, int):
                continue

            # Handle set courses
            # Get session
            try:
                i = user.schedule.index(c.session)
                ses = user.schedule[i]
            except ValueError:
                # Let this raise if not found
                i = user.free_sessions.index(c.session)
                ses = user.free_sessions.pop(i)

            # Add course to session and session to schedule
            ses.add_course(c)
            user.schedule.append(ses)
            user.schedule.sort()

        print("Set courses scheduled.")

    @classmethod
    def schedule_free(cls, user: User, restraints: Restraints) -> None:
        """Attempts to schedule all unassigned courses in accordance with
        restraints.
        
        Args:
            user (User): User instance with all potential Course objects in 
                attr 'user.courses'.
            restraints (Restraints): Restraints instance with all applicable 
                fields.

        Raises:
            SchedulingError: Raise when scheduling is impossible given current
                restraints.
        """
        r = restraints
        # Create temp and org vars for sorting
        courses = user.courses.copy()
        
        # Put actual course objs in inperson
        inperson = []
        if r.inperson_courses:
            for cid in r.inperson_courses:
                # DO NOT TRY/EXCEPT, LET IT RAISE
                i = courses.index(cid)
                c = courses.pop(i)

        if inperson: