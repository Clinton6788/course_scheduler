from __future__ import annotations
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

    @classmethod
    def create_all_sessions(
        cls, 
        user: User, 
        restraints: Restraints, 
        spread_between: int = None
    ) -> None:
        """Creates all possible sessions for User instance, based on 
        len(user.courses), Restraints.ses_min_class, and available GI Bill days.

        Args:
            user (User): User instance with all potential Course objects in 
                attr 'user.courses'.
            restraints (Restraints): Restraints instance with all applicable 
                fields.
            spread_between (int, optional): Total number of sessions to spread courses across.
        """
        from src.user import User
        print(f"Creating sessions for {user.id_}...")
        r = restraints
        u = user

        # Count courses by level
        under_count = sum(1 for c in u.courses if c.level == LevelENUM.UNDERGRAD)
        grad_count = sum(1 for c in u.courses if c.level == LevelENUM.GRADUATE)
        total_courses = under_count + grad_count

        # Determine session counts
        if spread_between:
            if total_courses == 0:
                under_ses = grad_ses = 0
            else:
                # Compute proportional sessions
                under_ses = max(int(spread_between * under_count / total_courses), 1 if under_count > 0 else 0)
                grad_ses = max(spread_between - under_ses, 1 if grad_count > 0 else 0)
        else:
            # Use max_per_ses to minimize extra sessions
            under_ses = (under_count + r.ses_max_class - 1) // r.ses_max_class
            grad_ses = (grad_count + r.ses_max_class - 1) // r.ses_max_class

            # Ensure at least 1 session if any courses exist
            under_ses = max(under_ses, 1) if under_count > 0 else 0
            grad_ses = max(grad_ses, 1) if grad_count > 0 else 0

        print(f"Calculated sessions -> Undergrad: {under_ses}, Grad: {grad_ses}")

        # Limit by GI Bill if exists
        if hasattr(u, "gib") and u.gib:
            session_days = SESSION_WEEKS * 7
            if r.exceed_benefits is False:
                max_sessions_possible = u.gib.get_remaining_days() // session_days
            else:
                max_sessions_possible = under_ses + grad_ses
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
        print("FULL SESSIONS")
        for s in full_sessions:
            print(f"{s.num}: {s.level}")

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
        from src.user import User
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
                print(f"-----Getting for {c.course_id}-----")
                print(user.schedule)
                print(user.free_sessions)
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
        under_courses = [c for c in user.courses if (
                c not in user.assigned_courses and c.level == LevelENUM.UNDERGRAD)]
        
        print(f"-----ASSIGNED---- {user.assigned_courses}")

        grad_courses = [c for c in user.courses if (
                c not in user.assigned_courses and c.level == LevelENUM.GRADUATE)]
        
        user.free_sessions = [s for s in user.free_sessions if s.start_date >= dt.date.today()]

        under_ses = [s for s in user.free_sessions if s.level == LevelENUM.UNDERGRAD]
        grad_ses = [s for s in user.free_sessions if s.level == LevelENUM.GRADUATE]
        print(f"________GRADSES:________\n{grad_ses}")
        print(f"_____________FREE SES__________")
        for s in user.free_sessions:
            print(f"\n{s.num}: {s.level}") 

        # Schedule undergrad first if avail:
        if under_courses or under_ses:
            if not (under_ses and under_courses):
                raise SchedulingError("Undergrad courses vs session discrepancy.")
            cls._schedule_level(user, under_courses, under_ses, restraints)

        # Schedule graduate if available
        if grad_courses or grad_ses:
            if not (grad_courses and grad_ses):
                print(f"Grad Courses: {grad_courses}\n Grad Ses: {grad_ses}")
                raise SchedulingError("Graduate courses vs session discrepancy.")
            cls._schedule_level(user, grad_courses, grad_ses, restraints)

        # --- Put Intent in correct Session ---
        # Get intent courses, map
        intent_courses = [c for c in user.courses if c.challenge_intent or c.transfer_intent]
        intent_map = {c.course_id: c for c in intent_courses}
        
        # Ensure sessions in order
        user.schedule.sort()

        # Start at index 1 since we want to store in previous session
        for i in range(1, len(user.schedule)):
            s_prev = user.schedule[i - 1]
            s_curr = user.schedule[i]

            for c in s_curr.courses:
                if not c.pre_reqs:
                    continue

                # Find which intent courses used in prereqs
                matched_ids = cls._extract_matching_prereqs(c.pre_reqs, set(intent_map))

                for matched_id in matched_ids:
                    s_prev.add_intent(intent_map[matched_id])
                    intent_map.pop(matched_id)            
        
        # Apply any leftover intents by spreading the load
        level = 1
        pending_ids = list(intent_map.keys())
        i = 0

        while pending_ids and i < 100:
            for course_id in pending_ids[:]:  # iterate over a copy
                course = intent_map[course_id]
                for session in user.schedule:
                    # Skip sessions that are already underway
                    if session.start_date <= dt.date.today():
                        continue
                    # Spread course into this session if under current level
                    if len(session.intent) <= level:
                        session.add_intent(course)
                        pending_ids.remove(course_id)
                        break  # move to next course
            level += 1
            i += 1

        if i >= 100:
            raise SchedulingError("Max iterations hit with intent courses")

    @classmethod
    def _schedule_level(
        cls,
        user: User,
        courses: list[Course], 
        sessions: list[Session],
        r: Restraints,
        tgt_list: list = None,
        recur = 0,
        ) -> None:
        """Internal method to handle individual scheduling. Must be called from schedule_free.
        Niave, assumes all validation has been passed.
        """
        # Assume all challenges are taken
        i = 0
        while i < len(courses):
            if courses[i].transfer_intent or courses[i].challenge_intent:
                user.assigned_courses.append(courses.pop(i))
            else:
                i += 1

        # Get targets
        if tgt_list is None:
            tgt_list = cls._get_course_targets(
                                len(courses),
                                len(sessions),
                                r.ses_min_class,
                                r.ses_max_class
                            )
        
        # Filter sessions to match tgt_list length
        sessions = sessions[:len(tgt_list)]

        print(f"{tgt_list=}")
        print(f"Total Courses:", len(courses))
        sessions.sort()
        courses.sort(reverse=True)

        gib = False
        if hasattr(user, "gib") and user.gib:
            gib = True

        print(f"--------SESSIONS-------{sessions}")

                
        # Schedule
        for i, s in enumerate(sessions):
            # Ensure inside min, max
            course_tgt = tgt_list[i]
            assert r.ses_min_class <= course_tgt <= r.ses_max_class, (
                f"Course count error||{course_tgt=}, {r.ses_max_class=}"
                f" {r.ses_min_class=}"
            )
            # Get pre-req qualified courses
            qual = cls._get_satisfied_prereqs(courses,user.assigned_courses)
            qual.sort(reverse=True)

            # Ensure inperson met
            if r.inperson_courses:
                if not r.in_person_end_dt:
                    raise SchedulingError("In person end date required for inperson scheduling")
                if s.start_date <= r.in_person_end_dt:
                    inperson = [c for c in qual if c in r.inperson_courses]
                    # Append to inperson if course already in session
                    for c in s.courses:
                        if c in r.inperson_courses:
                            inperson.append(c)
                    if r.min_inperson:
                        if len(inperson) < r.min_inperson:
                            raise SchedulingError("Not enough inperson courses")
                        if r.min_inperson > r.ses_max_class:
                            raise SchedulingError("Restraints: Min inperson > Max class")
                        for _ in range(r.min_inperson):
                            c = inperson.pop(0)
                            if c not in s.courses:
                                s.add_course(c)
                            qual.remove(c)

            # Create course list after inperson satisfied
            while len(s.courses) < course_tgt:
                print(f"Qualified for {s}: {[c.course_id for c in qual]}")
                if len(qual) < 1:
                    print(s.courses, qual, course_tgt)
                    raise SchedulingError(f"Out of pre-req qualified courses||{s}")
                c = qual.pop(0)
                if c not in s.courses:
                    s.add_course(c)

            # Last Verify
            assert len(s.courses) == course_tgt
                
            # Apply benefits
            s.add_grants(user.grants)
            if gib:
                covered, cost = user.gib.charge_session(s, final=True)
                # Ensure inside benefits
                if r.exceed_benefits is False and covered is False:
                    raise SchedulingError(f"Session exceeds benefits: {s=}")

            # Ensure inside max cost
            if r.ses_max_cost and cost > r.ses_max_cost:
                raise SchedulingError(f"Session outside cost restraint: {s=}")
            
            # Assign scheduled session and courses to user
            user.schedule.append(s)
            user.assigned_courses.extend(s.courses)

            # Remove scheduled courses and sessions
            # sessions.remove(s) # Causing skipping....Dumbass
            for c in s.courses:
                if c in courses:
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
        n_courses: int,
        n_sessions: int,
        min_per_ses: int,
        max_per_ses: int
    ) -> list[int]:
        """
        Distribute n_courses across n_sessions as evenly as possible,
        while respecting min_per_ses and max_per_ses.

        Returns a list of course counts per session.
        """

        if n_courses < n_sessions * min_per_ses:
            raise ValueError("Too few courses to meet minimum per session.")
        if n_courses > n_sessions * max_per_ses:
            raise ValueError("Too many courses to stay under maximum per session.")

        # Start with the floor division
        base = n_courses // n_sessions
        remainder = n_courses % n_sessions

        # Ensure base is within min/max bounds
        if base < min_per_ses:
            base = min_per_ses
            remainder = n_courses - base * n_sessions
        elif base > max_per_ses:
            base = max_per_ses
            remainder = n_courses - base * n_sessions

        targets = [base] * n_sessions

        # Distribute remainder one by one to first sessions that won't exceed max_per_ses
        i = 0
        while remainder > 0:
            if targets[i] < max_per_ses:
                targets[i] += 1
                remainder -= 1
            i = (i + 1) % n_sessions  # wrap around if needed

        # Final sanity check
        for t in targets:
            if not (min_per_ses <= t <= max_per_ses):
                raise ValueError("Cannot distribute courses within min/max bounds.")

        return targets
        

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
