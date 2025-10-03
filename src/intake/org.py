from src.scheduling.course import Course
from config.course_enums import (
    StatusENUM,
    LevelENUM,
    CourseFilterENUM as FILT
)
import pandas as pd
import re
from config.settings import CAPSTONE_PRIORITY, IN_PERSON_PRIORITY

def parse_prereqs(prereq_str: str) -> list:
    """
    Convert a prereq string like 'AND1|AND2|[OR1|OR2|OR3]|AND3'
    into a structured list:
    ['AND1', 'AND2', ['OR1','OR2','OR3'], 'AND3']
    Brackets are removed from strings, OR groups are preserved as sublists.
    """
    if not prereq_str or str(prereq_str).lower() in {"none", "nan"}:
        return []

    structured = []

    # Match either bracketed groups or single tokens
    pattern = re.compile(r'\[.*?\]|[^|]+')

    for match in pattern.findall(prereq_str):
        token = match.strip()
        if token.startswith('[') and token.endswith(']'):
            # OR group: split inside brackets
            or_group = [pr.strip() for pr in token[1:-1].split('|')]
            structured.append(or_group)
        else:
            structured.append(token)
    return structured

def create_courses(df: pd.DataFrame) -> list:
    print("Creating Courses")
    courses = []

    for _, row in df.iterrows():
        # Sanitize session
        session_val = row["session"]
        if pd.isna(session_val):  # NaN to None
            session_val = None
        elif isinstance(session_val, float) and session_val.is_integer():
            session_val = int(session_val)  # Convert 1.0 → 1
        elif isinstance(session_val, int):
            pass  # Already int
        else:
            session_val = None  # Anything else → None        
            
        c = Course(
            course_id=row["course id"],
            credit_hours=row["credit hours"],
            status=row["status"],
            level=row["level"],
            pre_reqs=parse_prereqs(row["prereqs"]),  
            capstone=row["capstone"],
            session=session_val,
            transfer_intent=row["transfer intent"],
            challenge_intent=row["challenge intent"]
        )
        
        courses.append(c)

    print(f"Courses Created||{len(courses)}")
    return courses

def organize_courses(courses:list)->dict:
    """Organizes by course level (grad, undergrad). 
    Args:
        courses (list): List of all Course objects. 
    Returns:
        dict: Dict with {LevelENUM: {Course.ID: Course OBJ,}}
    """
    print("Organizing Courses...")
    org_dict = {level.value: {} for level in LevelENUM}
    err = []

    for c in courses:
        try:
            level_enum = LevelENUM(c.level) # Valid
            org_dict[c.level][c.course_id] = c
        except ValueError:
            err.append(c.course_id)

    if not err:
        print("Organization Complete")
        return org_dict
    
    raise ValueError(f"Courses Wrong Level||{err}")

def prioritize_courses(courses: dict, in_person: list = []) -> list:
    """
    Prioritizes courses based on dependency count and in_person list.
    
    Args:
        courses (dict): MUST be flattened: {course_id: course_obj,}
        in_person (list): List of course IDs to be prioritized.

    Returns:
        list: List of priority sorted Course objects [Highest...Lowest]
    """
    print("Prioritizing Courses...")
    # Zero out priorities
    for c in courses.values():
        c.priority = 0

    pri_courses = topo_sort_with_priority(courses) 
    # Adjust for capstone, inperson
    for c in pri_courses:
        if c.capstone:
            c.priority -= CAPSTONE_PRIORITY
        if c in in_person:
            c.priority += IN_PERSON_PRIORITY

    return pri_courses


from collections import defaultdict, deque

def extract_flat_prereqs(prereqs):
    """Flatten AND/OR prereqs into a flat list of course_ids."""
    flat = []
    for p in prereqs:
        if isinstance(p, list):
            flat.extend(p)
        else:
            flat.append(p)
    return flat

def topo_sort_with_priority(courses: dict) -> list:
    """
    Topologically sort courses based on prereqs.
    Assign priority = depth. Ensures all prereqs appear before dependents.
    """
    from collections import defaultdict

    graph = defaultdict(list)
    visited = {}
    sorted_courses = []

    # Build graph: prereq -> dependent
    for cid, course in courses.items():
        flat_reqs = extract_flat_prereqs(course.pre_reqs)
        for pre in flat_reqs:
            graph[pre].append(cid)

    def dfs(course_id, depth=0):
        if course_id not in courses:
            return  # Prereq not in catalog
        if visited.get(course_id) == "temp":
            raise Exception(f"Cyclic dependency detected at {course_id}")
        if visited.get(course_id) == "perm":
            return

        visited[course_id] = "temp"
        max_depth = 0
        for dependent in graph[course_id]:
            dfs(dependent, depth + 1)
            max_depth = max(max_depth, courses[dependent].priority + 1)

        # Set depth as priority
        courses[course_id].priority = max(courses[course_id].priority, max_depth)
        visited[course_id] = "perm"
        sorted_courses.append(course_id)

    # Start DFS from all known courses
    for cid in courses:
        if visited.get(cid) is None:
            dfs(cid)



    # Return sorted Course objects by priority descending
    return sorted(courses.values(), key=lambda c: c.priority, reverse=True)

