


def generate_course_targets(
    min_courses: int,
    max_courses: int,
    under_course_count: int,
    grad_course_count: int,
    allow_single_last: bool = True,
    max_sessions: int | None = None,
    use_sessions: int | None = None,
):
    """
    Generate all valid course distributions across sessions for undergrad + grad courses.

    Args:
        min_courses (int): Minimum courses allowed per session.
        max_courses (int): Maximum courses allowed per session.
        under_course_count (int): Total number of undergrad courses.
        grad_course_count (int): Total number of graduate courses.
        allow_single_last (bool): Allow the final session in a level to have 1 course.
        max_sessions (int|None): Maximum number of sessions allowed in a schedule.
        use_sessions (int|None): Require exactly this many sessions in a schedule.

    Returns:
        list[list[int]]: All valid schedules as lists of session course counts.
    """