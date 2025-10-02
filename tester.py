from src.scheduling import Restraints, Session, Course



class testy:
    @classmethod    
    def schedule_free(cls, user: User, restraints: Restraints, spread_between: int = None) -> None:
        """
        Schedules all unassigned courses according to provided restraints.

        Args:
            user (User): User instance with courses.
            restraints (Restraints): All applicable scheduling constraints.
            spread_between (int): If an int is passed, sprease courses between <int> sessions.
                Default is None (Will not spread).

        Raises:
            SchedulingError: If scheduling cannot satisfy all constraints.
        """
        r = restraints
        remaining_courses = [c for c in user.courses if c not in user.assigned_courses]


        # Filter sessions that are in the past
        user.free_sessions = [s for s in user.free_sessions if s.start_date >= dt.date.today()]
        if not user.free_sessions:
            raise SchedulingError("No future sessions available for scheduling.")

        # Track in-person sessions
        inperson_count = sum(1 for s in user.schedule if getattr(s, "inperson", False))

        for course in remaining_courses:
            assigned = False

            # Sort sessions: prioritize earliest, least loaded
            sorted_sessions = sorted(
                user.free_sessions,
                key=lambda s: (len(s.courses), getattr(s, "total_cost", 0), s.start_date)
            )

            for ses in sorted_sessions:
                # ---- Constraint checks ----

                # Max classes per session
                if len(ses.courses) >= r.ses_max_class:
                    continue

                # Max cost
                total_cost = getattr(ses, "total_cost", 0) + course.tot_cost
                if r.ses_max_cost and total_cost > r.ses_max_cost:
                    continue

                # GI Bill days
                session_days = SESSION_WEEKS * 7
                if hasattr(user, "gib") and user.gib:
                    if not r.exceed_benefits and session_days > user.gib.get_remaining_days():
                        continue

                # In-person constraints
                if r.inperson_courses and course.name in r.inperson_courses:
                    # Check end date limit
                    if r.in_person_end_dt and ses.start_date > r.in_person_end_dt:
                        continue
                    # Check max in-person sessions
                    if r.max_inperson and inperson_count >= r.max_inperson:
                        continue
                    # Passed checks; mark session as in-person
                    ses.inperson = True
                    inperson_count += 1

                # Assign course to session
                ses.add_course(course)
                assigned = True
                break

            if not assigned:
                raise SchedulingError(f"Cannot schedule course '{course.name}' under current restraints.")

        # Move assigned sessions to schedule
        for ses in user.free_sessions:
            if ses.courses:
                user.schedule.append(ses)

        # Remove filled sessions from free_sessions
        user.free_sessions = [s for s in user.free_sessions if not s.courses]

        # Update assigned courses list
        user.assigned_courses.extend(remaining_courses)

        print(f"Scheduling complete for {user.id_}.")
