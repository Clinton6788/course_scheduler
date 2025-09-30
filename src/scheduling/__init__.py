from .course import Course
from .sessions import Session
from config.course_enums import LevelENUM
from config.settings import SESSION_MONTHS, SESSION_WEEKS
import datetime as dt

class SchedulingError(Exception):
    """Raised when a valid schedule cannot be created given the restraints."""
    pass


class Scheduler:
    from src.user import User, Restraints
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
        len(user.courses), Restraints.ses_min_class, and available GI Bill days.

        Args:
            user (User): User instance with all potential Course objects in 
                attr 'user.courses'.
            restraints (Restraints): Restraints instance with all applicable 
                fields.
        """
        print(f"Creating sessions for {user.id_}...")
        r = restraints
        u = user

        # Count courses by level
        under_count = sum(1 for c in u.courses if c.level == LevelENUM.UNDERGRAD)
        grad_count = sum(1 for c in u.courses if c.level == LevelENUM.GRADUATE)

        # Calculate required sessions (ceil division)
        under_ses = under_count // r.ses_min_class + (1 if under_count % r.ses_min_class else 0)
        grad_ses = grad_count // r.ses_min_class + (1 if grad_count % r.ses_min_class else 0)

        # Limit by GI Bill if exists
        if hasattr(u, "gib") and u.gib:
            session_days = SESSION_WEEKS * 7
            max_sessions_possible = u.gib.get_remaining_days() // session_days
            total_ses = under_ses + grad_ses

            if total_ses > max_sessions_possible:
                # Reduce proportionally per level
                if total_ses > 0:
                    under_ratio = under_ses / total_ses
                    grad_ratio = grad_ses / total_ses
                else:
                    under_ratio = grad_ratio = 0

                under_ses = int(max_sessions_possible * under_ratio)
                grad_ses = int(max_sessions_possible * grad_ratio)

                # Ensure at least one session if any courses exist
                under_ses = max(under_ses, 1) if under_count > 0 else 0
                grad_ses = max(grad_ses, 1) if grad_count > 0 else 0

        # Sort session months
        ses_months = sorted(SESSION_MONTHS)

        yr = u.first_ses_dt.year
        mo_index = ses_months.index(u.first_ses_dt.month)

        full_sessions = []
        ses_num = 1

        def generate_sessions(level: int, num_ses: int):
            nonlocal ses_num, mo_index, yr

            for _ in range(num_ses):
                mo = ses_months[mo_index]
                ses = Session(
                    ses_num,
                    dt.date(yr, mo, 1),
                    mo
                )
                ses.level = level
                full_sessions.append(ses)

                ses_num += 1
                mo_index += 1
                if mo_index >= len(ses_months):
                    mo_index = 0
                    yr += 1

        # Generate sessions per level
        generate_sessions(LevelENUM.UNDERGRAD, under_ses)
        generate_sessions(LevelENUM.GRADUATE, grad_ses)

        # Remove any existing sessions by number
        full_sessions = [s for s in full_sessions if s not in u.schedule]

        # Sort sessions by start date
        u.free_sessions = sorted(full_sessions, key=lambda s: s.start_date)

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
                ses = user.schedule.pop(i)
            except ValueError:
                # Let this raise if not found
                i = user.free_sessions.index(c.session)
                ses = user.free_sessions.pop(i)

            # Add course to session, session to schedule, course to 'assigned'
            ses.add_course(c)
            user.schedule.append(ses)
            user.schedule.sort()
            user.assigned_courses.append(c)


        print("Set courses scheduled.")

    @classmethod
    def schedule_free(cls, user: User, 
                    restraints: Restraints, 
                    use_all_sessions: bool = False) -> None:
        """Attempts to schedule all unassigned courses in accordance with
        restraints.
        
        Args:
            user (User): User instance with all potential Course objects in 
                attr 'user.courses'.
            restraints (Restraints): Restraints instance with all applicable 
                fields.
            use_all_sessions (bool): If True, spreads course load throughout
                all sessions; with ses_min_class acting as target.

        Raises:
            SchedulingError: Raise when scheduling is impossible given current
                restraints.
        """
        r = restraints
        # Create temp and org vars for sorting
        courses = user.courses.copy()
        scheduled = user.assigned_courses.copy()
        
        # Flags
        inperson = False
        if r.inperson_courses:
            if r.min_inperson and r.min_inperson > 0:
                inperson = True

        max_cost = True if r.ses_max_cost else False
        gib = True if user.gib else False

        # Remove scheduled from free courses
        for c in scheduled:
            i = courses.index(c)
            courses.pop(i)

        # Ensure current with sessions
        first_ses = user.free_sessions[0]
        if first_ses.start_date < dt.date.today():
            raise SchedulingError(f"First Session outside bounds: {first_ses.start_date}")
        
        # Ensure GIB up to date:
        # Treats any in-progress session as complete, charges accordingly
        if gib:
            completed = []
            for s in user.schedule:
                if s.start_date <= dt.date.today():
                    completed.append(s)
            user.gib.charge_historical(completed)

        # Begin Scheduling
        






