from __future__ import annotations
from .course import Course
from .sessions import Session
from .restraints import Restraints
from config.course_enums import LevelENUM, StatusENUM
from config.settings import SESSION_MONTHS, SESSION_WEEKS
from .pricing import get_pricing
import datetime as dt
from typing import Optional
import itertools

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

        # Count ALL courses by level (for proportional split)
        under_count = sum(1 for c in u.courses if c.level == LevelENUM.UNDERGRAD)
        grad_count = sum(1 for c in u.courses if c.level == LevelENUM.GRADUATE)
        total_courses = under_count + grad_count

        # Count FREE courses (not pre-assigned to a session, not completed without session)
        under_free = sum(1 for c in u.courses if c.level == LevelENUM.UNDERGRAD
                         and not isinstance(c.session, int) and c.status != StatusENUM.COMPLETED)
        grad_free = sum(1 for c in u.courses if c.level == LevelENUM.GRADUATE
                        and not isinstance(c.session, int) and c.status != StatusENUM.COMPLETED)

        # Sessions already consumed by set courses
        under_set_ses = len(set(c.session for c in u.courses
                               if c.level == LevelENUM.UNDERGRAD and isinstance(c.session, int)))
        grad_set_ses = len(set(c.session for c in u.courses
                               if c.level == LevelENUM.GRADUATE and isinstance(c.session, int)))

        # Minimum future sessions needed to fit free courses at max capacity
        under_future_min = (under_free + r.ses_max_class - 1) // r.ses_max_class if under_free > 0 else 0
        grad_future_min = (grad_free + r.ses_max_class - 1) // r.ses_max_class if grad_free > 0 else 0

        # Determine session counts (set sessions + enough future sessions)
        if spread_between:
            if total_courses == 0:
                under_ses = grad_ses = 0
            else:
                # Compute proportional sessions
                under_ses = max(int(spread_between * under_count / total_courses), 1 if under_count > 0 else 0)
                grad_ses = max(spread_between - under_ses, 1 if grad_count > 0 else 0)
                # Ensure enough future sessions beyond those used by set courses
                under_ses = max(under_ses, under_set_ses + under_future_min)
                grad_ses = max(grad_ses, grad_set_ses + grad_future_min)
        else:
            under_ses = max(under_set_ses + under_future_min, 1) if under_count > 0 else 0
            grad_ses = max(grad_set_ses + grad_future_min, 1) if grad_count > 0 else 0

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
        print(f"________GRADSES:________{grad_ses}")
        print(f"_____________FREE SES__________")
        for s in user.free_sessions:
            print(f"\n{s.num}: {s.level}") # ----------------------------------- All levels at 0 here

        # Schedule undergrad first if avail:
        if under_courses or under_ses:
            if not under_ses:
                raise SchedulingError(
                    f"Undergrad: {len(under_courses)} courses to schedule but 0 future sessions available. "
                    f"Check SPREAD_BETWEEN or session dates."
                )
            if not under_courses:
                raise SchedulingError(
                    f"Undergrad: {len(under_ses)} sessions allocated but 0 courses to schedule. "
                    f"All undergrad courses may already be assigned."
                )
            cls._schedule_level(user, under_courses, under_ses, restraints)

        # Schedule graduate if available
        if grad_courses or grad_ses:
            if not grad_ses:
                raise SchedulingError(
                    f"Graduate: {len(grad_courses)} courses to schedule but 0 future sessions available. "
                    f"Check SPREAD_BETWEEN or session dates."
                )
            if not grad_courses:
                raise SchedulingError(
                    f"Graduate: {len(grad_ses)} sessions allocated but 0 courses to schedule. "
                    f"All graduate courses may already be assigned."
                )
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
        max_iters = len(pending_ids) + len(user.schedule) + 1

        i = 0
        while pending_ids and i < max_iters:
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

        if pending_ids:
            raise SchedulingError(
                f"Could not distribute all intent courses: {pending_ids} remaining"
            )

    @classmethod
    def _schedule_level(
        cls,
        user: User,
        courses: list[Course],
        sessions: list[Session],
        r: Restraints,
        ) -> None:
        """Schedules courses into sessions using combinatorial backtracking.
        Tries multiple session counts (from minimum needed up to all available)
        and picks the schedule with the lowest estimated user cost.
        """
        # Strip challenge/transfer intent courses (treated as already complete)
        i = 0
        while i < len(courses):
            if courses[i].transfer_intent or courses[i].challenge_intent:
                user.assigned_courses.append(courses.pop(i))
            else:
                i += 1

        if not courses:
            return

        sessions.sort()
        courses.sort(reverse=True)
        has_gib = hasattr(user, "gib") and user.gib
        n_courses = len(courses)

        # Determine range of session counts to try
        # Account for courses already placed in sessions (from schedule_set)
        pre_placed = sum(len(s.courses) for s in sessions)
        total_to_hold = n_courses + pre_placed
        min_sessions = max(1, (total_to_hold + r.ses_max_class - 1) // r.ses_max_class)
        max_sessions = len(sessions)
        grant_amount = user.grants.get(sessions[0].level, 0)

        # Try each possible session count, collect valid results
        candidates = []
        level_name = "Undergrad" if sessions[0].level == LevelENUM.UNDERGRAD else "Graduate"
        rejection_reasons = []

        for n_ses in range(min_sessions, max_sessions + 1):
            # Enumerate session subsets: try different combinations of which
            # sessions to use (not just the first N). This matters when
            # benefit-year boundaries or GIB day limits interact with session dates.
            session_subsets = cls._enumerate_session_subsets(sessions, n_ses)

            found_zero_cost = False
            for trial_sessions in session_subsets:
                pre_placed_in_trial = sum(len(s.courses) for s in trial_sessions)
                total_in_trial = n_courses + pre_placed_in_trial

                sorted_distributions = cls._enumerate_target_distributions(
                    total_in_trial, n_ses, r.ses_min_class, r.ses_max_class
                )
                if not sorted_distributions:
                    continue

                seen_tgts = set()
                for sorted_dist in sorted_distributions:
                    for tgt_list in itertools.permutations(sorted_dist):
                        if tgt_list in seen_tgts:
                            continue
                        seen_tgts.add(tgt_list)
                        tgt_list = list(tgt_list)

                        result = cls._backtrack_schedule(
                            courses=list(courses),
                            sessions=trial_sessions,
                            tgt_list=tgt_list,
                            r=r,
                            has_gib=has_gib,
                            user=user,
                            session_idx=0,
                            assigned=list(user.assigned_courses),
                        )
                        if result is None:
                            continue

                        estimated_user_cost = cls._estimate_user_cost(
                            result, grant_amount, user, has_gib
                        )
                        candidates.append((estimated_user_cost, result))

                        if estimated_user_cost == 0:
                            found_zero_cost = True
                            break
                    if found_zero_cost:
                        break
                if found_zero_cost:
                    break

            # Report best candidate found for this session count
            best_for_n = min(
                (c for c in candidates if len(c[1]) == n_ses),
                default=None,
                key=lambda x: x[0],
            )
            if best_for_n is not None:
                print(f"  [best @ {n_ses} sessions] est_user_cost={best_for_n[0]:.0f}")
            else:
                rejection_reasons.append(
                    f"{n_ses} sessions: no valid schedule found across any subset/distribution"
                )

            # Early exit the outer loop if we found $0
            if found_zero_cost:
                break

        if not candidates:
            reasons = "\n  ".join(rejection_reasons) if rejection_reasons else "No session counts were valid"
            raise SchedulingError(
                f"{level_name}: No valid schedule found for {n_courses} courses "
                f"across {min_sessions}-{max_sessions} sessions "
                f"(min={r.ses_min_class}, max={r.ses_max_class}).\n"
                f"  Rejection details:\n  {reasons}"
            )

        # Pick cheapest
        candidates.sort(key=lambda x: x[0])
        best_cost, best_result = candidates[0]
        n_used = len(best_result)
        print(f"  [selected] {n_used} sessions, est_cost={best_cost:.0f}")

        # Apply the best schedule
        cls._apply_schedule_result(user, best_result, r, has_gib)

    # Maximum combos to try per session before giving up on alternatives.
    # The best-priority combos are tried first, so this bounds the search
    # while still allowing backtracking for prerequisite-blocked paths.
    MAX_COMBOS_PER_SESSION = 5

    @classmethod
    def _backtrack_schedule(
        cls,
        courses: list[Course],
        sessions: list[Session],
        tgt_list: list[int],
        r: Restraints,
        has_gib: bool,
        user: User,
        session_idx: int,
        assigned: list[Course],
    ) -> list[tuple[Session, list[Course]]] | None:
        """Recursive backtracking search for a valid course-to-session assignment.

        Returns a list of (session, chosen_courses) tuples on success, or None
        if no valid assignment exists from this point forward.
        """
        # Base case: all sessions filled
        if session_idx >= len(sessions):
            if not courses:
                return []
            return None  # Leftover courses — invalid

        s = sessions[session_idx]
        tgt = tgt_list[session_idx]

        # Forward check: enough courses remain to fill all future sessions?
        # Subtract courses already placed in sessions (from schedule_set)
        future_needed = sum(tgt_list[session_idx:]) - sum(
            len(sessions[i].courses) for i in range(session_idx, len(sessions))
            if i < len(tgt_list)
        )
        if len(courses) < future_needed:
            return None

        # Account for courses already in session (from schedule_set)
        already_in = len(s.courses)
        needed = tgt - already_in
        if needed <= 0:
            # Session already full from set courses, recurse to next
            result = cls._backtrack_schedule(
                courses, sessions, tgt_list, r, has_gib, user,
                session_idx + 1, assigned,
            )
            if result is not None:
                return [(s, [])] + result
            return None

        # Get prereq-qualified courses from remaining pool
        qualified = cls._get_satisfied_prereqs(courses, assigned)

        if len(qualified) < needed:
            return None  # Not enough qualified courses for this session

        # Generate valid combinations of size `needed`, bounded and priority-sorted
        valid_combos = cls._generate_valid_combinations(
            qualified, needed, s, assigned, user, r, has_gib,
        )

        # Try each combo in priority order (best-first), bounded
        for combo in valid_combos[:cls.MAX_COMBOS_PER_SESSION]:
            combo_ids = {c.course_id for c in combo}
            remaining = [c for c in courses if c.course_id not in combo_ids]
            new_assigned = assigned + list(combo)

            # Forward check: verify the next session has enough qualified courses
            if session_idx + 1 < len(sessions):
                next_needed = tgt_list[session_idx + 1] - len(sessions[session_idx + 1].courses)
                if next_needed > 0:
                    next_qual = cls._get_satisfied_prereqs(remaining, new_assigned)
                    if len(next_qual) < next_needed:
                        continue  # This combo blocks the next session — skip

            result = cls._backtrack_schedule(
                remaining, sessions, tgt_list, r, has_gib, user,
                session_idx + 1, new_assigned,
            )
            if result is not None:
                return [(s, list(combo))] + result

        return None  # All combos exhausted — backtrack

    @classmethod
    def _estimate_user_cost(
        cls,
        result: list[tuple[Session, list[Course]]],
        grant_amount: float,
        user: User,
        has_gib: bool,
    ) -> float:
        """Estimate total user out-of-pocket cost for a candidate schedule.
        Simulates GIB day and dollar consumption per benefit year.
        """
        from dateutil.relativedelta import relativedelta

        session_duration = SESSION_WEEKS * 7 + 1
        sim_days = user.gib.remaining_days if has_gib else 0

        # Build simulated benefit year balances (copy, don't mutate)
        sim_years = {}
        if has_gib:
            for ys, by in user.gib.benefit_years.items():
                sim_years[ys] = by.amount
            benefit_month = user.gib.benefit_start.month
            benefit_day = user.gib.benefit_start.day

        estimated_user_cost = 0.0
        for ses, combo in result:
            ses_cost = sum(c.cost_on(ses.start_date) for c in combo) + get_pricing(ses.start_date).cost_per_session
            after_grants = max(0, ses_cost - grant_amount)

            if has_gib and sim_days > 0:
                sim_days = max(0, sim_days - session_duration)

                # Resolve benefit year for this session
                year_start = ses.start_date.replace(
                    month=benefit_month, day=benefit_day
                )
                if ses.start_date < year_start:
                    year_start = year_start.replace(year=year_start.year - 1)
                if year_start not in sim_years:
                    sim_years[year_start] = user.gib.yearly_amount

                # Apply dollar coverage
                coverage = min(after_grants, sim_years[year_start])
                sim_years[year_start] -= coverage
                estimated_user_cost += after_grants - coverage
            else:
                estimated_user_cost += after_grants

        return estimated_user_cost

    @classmethod
    def _generate_valid_combinations(
        cls,
        qualified: list[Course],
        target_count: int,
        session: Session,
        completed: list[Course],
        user: User,
        r: Restraints,
        has_gib: bool,
    ) -> list[tuple[Course, ...]]:
        """Generate all valid course combinations for a session, sorted by
        total priority descending (highest-priority combo first).
        """
        valid = []
        for combo in itertools.combinations(qualified, target_count):
            if cls._validate_session_assignment(combo, session, completed, user, r, has_gib):
                valid.append(combo)

        # Sort by sum of priorities, highest first
        valid.sort(key=lambda c: sum(course.priority for course in c), reverse=True)
        return valid

    @classmethod
    def _validate_session_assignment(
        cls,
        candidates: tuple[Course, ...],
        session: Session,
        completed: list[Course],
        user: User,
        r: Restraints,
        has_gib: bool,
    ) -> bool:
        """Check whether a set of candidate courses satisfies all constraints
        for the given session. Non-destructive (does not mutate state).
        """
        # 1. Prerequisites — each candidate must have prereqs met
        for c in candidates:
            for pre in c.pre_reqs:
                if isinstance(pre, list):  # OR group
                    if not any(p in completed for p in pre):
                        return False
                else:  # AND prerequisite
                    if pre not in completed:
                        return False

        # 2. In-person constraints
        if r.inperson_courses and r.in_person_end_dt:
            if session.start_date <= r.in_person_end_dt:
                inperson_count = sum(1 for c in candidates if c.course_id in r.inperson_courses)
                # Also count courses already in session
                inperson_count += sum(1 for c in session.courses if c.course_id in r.inperson_courses)

                if r.min_inperson and inperson_count < r.min_inperson:
                    return False
                if r.max_inperson and inperson_count > r.max_inperson:
                    return False

        # 3. Capstone check — capstone courses should not appear in non-final sessions
        #    (This is soft — handled by priority, but capstones with unmet prereqs
        #    are naturally excluded by the prereq check above)

        return True

    @classmethod
    def _apply_schedule_result(
        cls,
        user: User,
        result: list[tuple[Session, list[Course]]],
        r: Restraints,
        has_gib: bool,
    ) -> None:
        """Materialize a backtracking result: add courses to sessions,
        apply grants/GIB, and assign to user schedule.
        """
        for session, courses in result:
            for c in courses:
                if c not in session.courses:
                    session.add_course(c)

            session.add_grants(user.grants.get(session.level, 0))

            cost = session.adj_cost
            if has_gib:
                covered, cost = user.gib.charge_session(session, final=True)
                if r.exceed_benefits is False and covered is False:
                    raise SchedulingError(f"Session exceeds benefits: {session}")

            if r.ses_max_cost and cost > r.ses_max_cost:
                raise SchedulingError(f"Session outside cost restraint: {session}")

            user.schedule.append(session)
            user.assigned_courses.extend(courses)

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

    # Cap total session subsets to prevent combinatorial explosion with many
    # available sessions. When exceeded, we fall back to a sampled set of subsets.
    MAX_SESSION_SUBSETS = 30

    @classmethod
    def _enumerate_session_subsets(
        cls,
        sessions: list[Session],
        n_ses: int,
    ) -> list[list[Session]]:
        """Enumerate which subsets of `sessions` to consider when using n_ses of them.
        Different subsets can produce different costs because sessions have fixed
        dates that interact with GIB benefit year boundaries and day limits.

        When all subsets fit under MAX_SESSION_SUBSETS, returns all of them.
        Otherwise returns a sampled set that prioritizes prefix, suffix, and
        single-skip variants (which are the most impactful for benefit-year splits).
        """
        if n_ses > len(sessions):
            return []
        if n_ses == len(sessions):
            return [list(sessions)]

        import math
        total = math.comb(len(sessions), n_ses)
        if total <= cls.MAX_SESSION_SUBSETS:
            return [list(combo) for combo in itertools.combinations(sessions, n_ses)]

        # Sampled: prefix, suffix, then each single-skip variant
        results = []
        seen = set()

        def add(subset):
            key = tuple(s.num for s in subset)
            if key not in seen:
                seen.add(key)
                results.append(list(subset))

        # Prefix
        add(sessions[:n_ses])
        # Suffix
        add(sessions[-n_ses:])
        # Every possible single-session skip (drop one, keep n_ses)
        for skip_idx in range(len(sessions)):
            subset = [s for i, s in enumerate(sessions) if i != skip_idx]
            if len(subset) >= n_ses:
                add(subset[:n_ses])
                add(subset[-n_ses:])
            if len(results) >= cls.MAX_SESSION_SUBSETS:
                break

        return results

    @classmethod
    def _enumerate_target_distributions(
        cls,
        n_courses: int,
        n_sessions: int,
        min_per_ses: int,
        max_per_ses: int,
    ) -> list[tuple[int, ...]]:
        """Enumerate ALL valid sorted (descending) distributions of n_courses
        across n_sessions where each session has between min_per_ses and
        max_per_ses courses.

        Returns a list of sorted tuples. Caller should permute each tuple to
        try different placements.
        """
        results = []

        def recurse(remaining_courses: int, remaining_sessions: int,
                    max_allowed: int, current: list[int]) -> None:
            if remaining_sessions == 0:
                if remaining_courses == 0:
                    results.append(tuple(current))
                return
            # Each future session value is bounded by min_per and max_allowed
            # Lower bound: enough to not leave too many for future sessions
            min_v = max(min_per_ses, remaining_courses - (remaining_sessions - 1) * max_allowed)
            # Upper bound: don't use more than allowed, and leave at least min_per for others
            max_v = min(max_allowed, remaining_courses - (remaining_sessions - 1) * min_per_ses)
            if min_v > max_v:
                return
            for v in range(max_v, min_v - 1, -1):
                recurse(remaining_courses - v, remaining_sessions - 1, v, current + [v])

        recurse(n_courses, n_sessions, max_per_ses, [])
        return results

    @classmethod
    def _get_course_targets(
        cls,
        n_courses: int,
        n_sessions: int,
        min_per_ses: int,
        max_per_ses: int
    ) -> list[int] | None:
        """
        Distribute n_courses across n_sessions as evenly as possible,
        while respecting min_per_ses and max_per_ses.

        Returns a list of course counts per session, or None if impossible.
        """

        if n_courses < n_sessions * min_per_ses:
            return None
        if n_courses > n_sessions * max_per_ses:
            return None

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
                return None

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
