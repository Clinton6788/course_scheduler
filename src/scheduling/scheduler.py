from .course import Course
from .sessions import Session
from .restraints import Restraints
from config.course_enums import LevelENUM, StatusENUM
from config.settings import SESSION_MONTHS, SESSION_WEEKS
import datetime as dt
from typing import Optional

class SchedulingError(Exception):
    """Raised when a valid schedule cannot be created given the restraints."""
    pass


class Scheduler:
    from src.user import User
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

        # Calculate required sessions
        under_ses = under_count // r.ses_min_class + (1 if under_count % r.ses_min_class else 0)
        grad_ses = grad_count // r.ses_min_class + (1 if grad_count % r.ses_min_class else 0)

        # Limit by GI Bill if exists
        if hasattr(u, "gib") and u.gib:
            session_days = SESSION_WEEKS * 7
            max_sessions_possible = u.gib.get_remaining_days() // session_days
            total_ses = under_ses + grad_ses

            if total_ses > max_sessions_possible:
                if r.exceed_benefits is False:
                    raise SchedulingError(f"Schedule will exceed benefits||"
                                        f"{total_ses=}||{max_sessions_possible=}")
                

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
        """Schedules all Courses with 'set' session number and "completes" all
        courses with status "StatusENUM.COMPLETE". This includes 
        statuses: 'complete' and 'inprocess', assuming proper intake format. 
        Modifies 'User' inplace. Ensure 'create_all_sessions' called first.

        Args:
            user (User): User instance with all potential Course objects in 
                attr 'user.courses'.
        """
        print(f"Scheduling set courses for {user.id_}...")

        # Find set courses
        for c in user.courses:
            if not isinstance(c.session, int):
                if c.status == StatusENUM.COMPLETED:
                    user.assigned_courses.append(c)
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
            if ses.start_date < dt.date.today():
                user.schedule.append(ses)
            else:
                user.free_sessions.append(ses)
            user.assigned_courses.append(c)
        
        # Ensure sorted sessions
        user.free_sessions.sort()
        user.schedule.sort()


        print("Set courses scheduled.")

    @classmethod
    def schedule_free(
        cls, 
        user: User, 
        restraints: Restraints, 
        ) -> None:
        """
        Schedules all unassigned courses according to provided restraints. Assumes pre-assigned
        sessions (create_all_sessions, plan_session_levels).

        Args:
            user (User): User instance with courses.
            restraints (Restraints): All applicable scheduling constraints.

        Raises:
            SchedulingError: If scheduling cannot satisfy all constraints.
        """
        # Clean up and copy for scheduling use
        r = restraints
        under_courses = [c for c in user.courses if c not in user.assigned_courses and c.level == LevelENUM.UNDERGRAD]
        grad_courses = [c for c in user.courses if c not in user.assigned_courses and c.level == LevelENUM.GRADUATE]
        user.free_sessions = [s for s in user.free_sessions if s.start_date >= dt.date.today()]
        under_ses = [s for s in user.free_sessions if s.level == LevelENUM.UNDERGRAD]
        grad_ses = [s for s in user.free_sessions if s.level == LevelENUM.GRADUATE]

        # Schedule undergrad first if avail:
        if under_courses or under_ses:
            if not (under_ses and under_courses):
                raise SchedulingError("Undergrad courses vs session discrepancy.")
            cls._schedule_level(user, under_courses, under_ses, restraints)

        # Schedule graduate if available
        if grad_courses or grad_ses:
            if not (grad_courses and grad_ses):
                raise SchedulingError("Graduate courses vs session discrepancy.")
            cls._schedule_level(user, grad_courses, grad_ses, restraints)

        # --- Put Intent in correct Session ---
        # Get intent courses, map
        intent_courses = [c for c in user.courses if c.challenge_intent or c.transfer_intent]
        intent_map = {c.id: c for c in intent_courses}
        
        # Ensure sessions in order
        user.schedule.sort()

        # Start at index 1 since we want to store in previous session
        for i in range(1, len(user.schedule)):
            s_prev = user.schedule[i - 1]
            s_curr = user.schedule[i]

            for c in s_curr.courses:
                if not c.prereqs:
                    continue

                # Find which intent courses used in prereqs
                matched_ids = cls._extract_matching_prereqs(c.prereqs, set(intent_map))

                for matched_id in matched_ids:
                    s_prev.add_intent(intent_map[matched_id])
                    intent_map.pop(matched_id)            

    @classmethod
    def _schedule_level(
        cls,
        user: User,
        courses: list[Course], 
        sessions: list[Session],
        r: Restraints,
        ) -> None:
        """Internal method to handle individual scheduling. Must be called from schedule_free.
        Niave, assumes all validation has been passed.
        """
        # Get targets
        tgt_list = cls._get_course_targets(
                            len(courses),
                            len(sessions),
                            r.ses_min_class,
                            r.ses_max_class
                        )

        sessions.sort()
        courses.sort()

        gib = False
        if hasattr(user, "gib") and user.gib:
            gib = True

        user.assigned_courses
        
        # Assume all challenges are taken
        i = 0
        while i < len(courses):
            if courses[i].transfer_intent or courses[i].challenge_intent:
                user.assigned_courses.append(courses.pop(i))
            else:
                i += 1

                
        # Schedule
        for i, s in enumerate(sessions):
            ses_courses = []
            # Ensure inside min, max
            course_tgt = tgt_list[i]
            assert r.ses_min_class <= course_tgt <= r.ses_max_class, (
                f"Course count error||{course_tgt=}, {r.ses_max_class=}"
                f" {r.ses_min_class=}"
            )
            # Get pre-req qualified courses
            qual = cls._get_satisfied_prereqs(courses,user.assigned_courses)
            qual.sort()

            # Ensure inperson met
            if r.inperson_courses:
                if not r.in_person_end_dt:
                    raise SchedulingError("In person end date required for inperson scheduling")
                if s.start_date <= r.in_person_end_dt:
                    inperson = [c for c in qual if c in r.inperson_courses]
                    if r.min_inperson:
                        if len(inperson) < r.min_inperson:
                            raise SchedulingError("Not enough inperson courses")
                        if r.min_inperson > r.ses_max_class:
                            raise SchedulingError("Restraints: Min inperson > Max class")
                        for _ in range(r.min_inperson):
                            c = inperson.pop(0)
                            ses_courses.append(c)
                            qual.remove(c)

            # Create course list after inperson satisfied
            while len(ses_courses) < course_tgt:
                if len(qual) < 1:
                    raise SchedulingError(f"Out of pre-req qualified courses||{s}")
                c = qual.pop(0)
                ses_courses.append(c)

            # Last Verify
            assert len(ses_courses) == course_tgt

            # Store inside session
            for c in ses_courses:
                s.add_course(c)
                
            # Apply benefits
            cost = s.tot_cost
            s.adj_cost = cost - user.grants if cost > user.grants else 0
            if gib:
                covered, cost = user.gib.charge_session(s)
                # Ensure inside benefits
                if r.exceed_benefits is False and covered is False:
                    raise SchedulingError(f"Session exceeds benefits: {s=}")
                s.adj_cost = cost

            # Ensure inside max cost
            if r.ses_max_cost and cost > r.ses_max_cost:
                raise SchedulingError(f"Session outside cost restraint: {s=}")
            
            # If gib, finalize charge
            user.gib.charge_session(s, True)

            # Assign scheduled session and courses to user
            user.schedule.append(s)
            user.assigned_courses.extend(ses_courses)

            # Remove scheduled courses and sessions
            sessions.remove(s)
            for c in ses_courses:
                courses.remove(c)

    @classmethod
    def _get_satisfied_prereqs(
        cls, 
        courses: list[Course], 
        completed: list[Course],
        ) -> list[Course]:
        """
        Returns a list of courses with prereqs met.
        """
        satisfied = []
        for c in courses:
            met = True
            for pre in c.pre_reqs:
                if isinstance(pre, list):  # OR group
                    if not any(p in completed for p in pre):
                        met = False
                else:  # AND prerequisite
                    if pre not in completed:
                        met = False
            if met:
                satisfied.append(c)

        return satisfied

    @classmethod
    def _get_course_targets(
        cls,
        n_courses, 
        n_sessions, 
        min_per_ses, 
        max_per_ses):
        # Early checks
        if n_courses < n_sessions * min_per_ses:
            raise ValueError("Too few courses to meet minimum per session.")
        if n_courses > n_sessions * max_per_ses:
            raise ValueError("Too many courses to stay under maximum per session.")

        # Start with floor division
        base = n_courses // n_sessions
        remainder = n_courses % n_sessions

        targets = [base] * n_sessions

        # Distribute the remainder without exceeding max_per_ses
        for i in range(remainder):
            if targets[i] < max_per_ses:
                targets[i] += 1
            else:
                # Overflow, find next session that can accept more
                for j in range(i+1, n_sessions):
                    if targets[j] < max_per_ses:
                        targets[j] += 1
                        break

        # Final check (optional safety)
        for t in targets:
            if not (min_per_ses <= t <= max_per_ses):
                raise ValueError("Cannot distribute courses within min/max bounds.")

        return targets
        
    @classmethod
    def _plan_session_levels(
        cls,
        user: User, 
        restraints: Restraints, 
        spread_between: Optional[int] = None
        ) -> None:
        """
        Assigns level to sessions in user.free_sessions after session creation AND set courses scheduled.

        Args:
            user (User): User instance with free_sessions created.
            restraints (Restraints): Scheduling constraints.
            spread_between (int, optional): If provided, will spread across a fixed number of sessions.
        """
        r = restraints
        under_count = sum(1 for c in user.courses if c.level == LevelENUM.UNDERGRAD and not c.session)
        grad_count = sum(1 for c in user.courses if c.level == LevelENUM.GRADUATE and not c.session)
        total_courses = under_count + grad_count

        if total_courses == 0:
            return  # No levels to assign

        # Determine session count
        if spread_between and spread_between > 0:
            total_sessions = spread_between
        else:
            under_ses = (under_count + r.ses_min_class - 1) // r.ses_min_class
            grad_ses = (grad_count + r.ses_min_class - 1) // r.ses_min_class
            total_sessions = under_ses + grad_ses

        # Limit by GI Bill
        if hasattr(user, "gib") and user.gib and not r.exceed_benefits:
            session_days = SESSION_WEEKS * 7
            max_sessions = user.gib.get_remaining_days() // session_days
            total_sessions = min(total_sessions, max_sessions)

        # Get actual sessions to plan
        sessions = [s for s in user.free_sessions if s.start_date >= dt.date.today()]
        if total_sessions < len(sessions):
            sessions = sessions[:total_sessions]

        # Compute session counts by level
        under_ratio = under_count / total_courses if total_courses else 0
        grad_ratio = grad_count / total_courses if total_courses else 0

        under_ses = round(total_sessions * under_ratio)
        grad_ses = total_sessions - under_ses

        # Assign levels to sessions
        for i, s in enumerate(sessions):
            s.level = LevelENUM.UNDERGRAD if i < under_ses else LevelENUM.GRADUATE

    @classmethod
    def _extract_matching_prereqs(cls, prereqs: list, intent_ids):
        """Return a set of intent_ids that appear in the prereqs structure."""
        found = set()
        for p in prereqs:
            if isinstance(p, list):
                found.update(cls._extract_matching_prereqs(p, intent_ids))
            elif p in intent_ids:
                found.add(p)
        return found
