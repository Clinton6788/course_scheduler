def get_courses_pipeline(
        course_path: str,
        course_path_abs: bool,
        in_person: list|None|str = None,
        ) -> list:
    """
    Process raw course data through the full pipeline:  
    1. Load from Excel  
    2. Create Course objects  
    3. Organize by level  
    4. Prioritize courses  

    Args:
        in_person (list): Optional list of course IDs to treat as in-person for filtering logic.

    Returns:
        courses: List of Course objects
    """
    # Imports to avoid high-level exposure
    from src.intake import (
        fetch_data,
        create_courses,
        organize_courses,
        prioritize_courses
    )
    # Quick Validation:
    msg = "Get Courses Pipeline||Improper Arg: "
    assert isinstance(course_path, str), f"{msg} course_path: {type(course_path)}"
    assert isinstance(course_path_abs, bool), f"{msg} course_path_abs: {type(course_path_abs)}"
    if in_person == None:
        in_person = []
    elif isinstance(in_person, str):
        raise NotImplementedError(f"{msg} STR path for in_person not supported yet")
    elif isinstance(in_person, list):
        assert (all(isinstance(x, str) for x in in_person) or in_person == []), f"{msg} in_person contents: {in_person}"
    else:
        raise TypeError(f"{msg} in_person: {type(in_person)}")

    raw_df = fetch_data(course_path, is_absolute=course_path_abs)

    # Flattened list of Course objects
    all_classes_list = create_courses(raw_df)

    # Organize courses by LevelENUM
    org_by_level_dict = organize_courses(all_classes_list)
    # {LevelENUM: {Course.course_id: Course obj, ...}, ...}

    # Prioritize courses per level
    
    prioritized_dict = {
        k: prioritize_courses(v,in_person=in_person)
        for k, v in org_by_level_dict.items()
    }

    out = []
    for _, l in prioritized_dict.items():
        out.extend(l)

    return out
