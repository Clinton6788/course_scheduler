@classmethod
def schedule_set(cls, user: User, restraints: Restraints) -> None:
    """
    Schedule all courses with a predefined 'set' session number.
    Updates the GI Bill before assignment, ensures sessions exist, and respects restraints.

    Args:
        user (User): User instance with courses.
        restraints (Restraints): Scheduling constraints.
    """
    print(f"Scheduling set courses for {user.id_}...")

    # Ensure GI Bill is up-to-date
    if hasattr(user, "gib") and user.gib:
        completed = [s for s in user.schedule if s.start_date <= dt.date.today()]
        user.gib.charge_historical(completed)

    # Ensure free sessions exist
    if not user.free_sessions:
        cls.create_all_sessions(user, restraints)

    # Filter out past sessions
    user.free_sessions = [s for s in user.free_sessions if s.start_date >= dt.date.today()]

    assigned_courses = []

    for course in user.courses:
        # Skip courses without a set session
        if not isinstance(course.session, int):
            continue

        # Find the session object
        ses = next(
            (s for s in user.schedule + user.free_sessions if s.ses_num == course.session),
            None
        )
        if not ses:
            raise SchedulingError(f"Set session {course.session} not found for course '{course.name}'.")

        # Constraint checks
        if restraints.ses_max_class and len(ses.courses) >= restraints.ses_max_class:
            raise SchedulingError(f"Session {ses.ses_num} already has max classes.")

        if hasattr(user, "gib") and user.gib:
            session_days = SESSION_WEEKS * 7
            if not restraints.exceed_benefits and session_days > user.gib.get_remaining_days():
                raise SchedulingError(f"GI Bill days insufficient for session {ses.ses_num}.")

        if restraints.ses_max_cost and (getattr(ses, "total_cost", 0) + course.tot_cost) > restraints.ses_max_cost:
            raise SchedulingError(f"Session {ses.ses_num} would exceed max cost.")

        # In-person handling
        if restraints.inperson_courses and course.name in restraints.inperson_courses:
            if restraints.in_person_end_dt and ses.start_date > restraints.in_person_end_dt:
                raise SchedulingError(f"Cannot schedule '{course.name}' after in-person cutoff.")
            ses.inperson = True

        # Assign course
        ses.add_course(course)
        assigned_courses.append(course)

        # Move session to schedule if it was in free_sessions
        if ses in user.free_sessions:
            user.free_sessions.remove(ses)
            user.schedule.append(ses)

    # Update user's assigned courses
    user.assigned_courses.extend(assigned_courses)

    # Sort schedule for consistency
    user.schedule.sort(key=lambda s: s.start_date)

    print(f"Set courses scheduled for {user.id_}.")
