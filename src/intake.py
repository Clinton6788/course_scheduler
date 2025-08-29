import pandas as pd
from src.courses import Course
from course_enums import StatusENUM, LevelENUM, CourseFilterENUM as FILT
from settings import (
    SESSIONS, 
    IN_PERSON_PRIORITY,
)
from src.helpers import prereq_total_count


# region Intake
# Mapping of possible column variations → standardized lowercase column names
COLUMN_MAP = {
    "course id": ["course id", "courseid", "course_id", "Course ID", "COURSEID"],
    "credit hours": ["credit hours", "credithours", "credit_hours", "Credit Hours", "CREDITHOURS"],
    "status": ["status", "Status", "STATUS"],
    "level": ["level", "Level", "LEVEL"],
    "prereqs": ["prereqs", "Prereqs", "PREREQS", "pre-reqs", "pre_reqs"],
    "capstone": ["capstone", "Capstone", "CAPSTONE"],
    "session": ["session", "Session", "SESSION"],
    "sophia avail": ["sophia avail", "Sophia Avail", "sophia_avail"],
    "sophia intent": ["sophia intent", "Sophia Intent", "sophia_intent"],
    "challenge avail": ["challenge avail", "Challenge Avail", "challenge_avail"],
    "challenge intent": ["challenge intent", "Challenge Intent", "challenge_intent"],
}

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map any variant column names to standard lowercase names."""
    new_cols = {}
    for std_name, variants in COLUMN_MAP.items():
        for v in variants:
            if v in df.columns:
                new_cols[v] = std_name
    df = df.rename(columns=new_cols)
    # Force all column names to lowercase and strip spaces
    df.columns = df.columns.str.strip().str.lower()
    return df

def normalize_prereqs(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize the 'prereqs' column: commas to pipes, remove spaces, fix NaNs."""
    if "prereqs" not in df.columns:
        print("NO PREREQS")
        return df

    def clean(val):
        if pd.isna(val) or str(val).strip() == "":
            return ""
        # Ensure string, strip leading/trailing, replace commas
        val = str(val).strip().replace(",", "|")
        # Clean each part
        parts = [p.strip() for p in val.split("|") if p.strip()]
        return "|".join(parts)

    df["prereqs"] = df["prereqs"].apply(clean)
    return df


def validate_df(df: pd.DataFrame):
    """Validates that the DataFrame has required columns and correct formats."""
    print("Validating DataFrame")
    df = normalize_columns(df)

    required_columns = list(COLUMN_MAP.keys())

    # 1. Check columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # 2. credit hours must be int
    if not pd.api.types.is_integer_dtype(df["credit hours"]):
        raise TypeError("'credit hours' must be integers")

    # 3. status must be in StatusENUM
    invalid_status = df.loc[~df["status"].isin([e.value for e in StatusENUM]), "status"]
    if not invalid_status.empty:
        raise ValueError(f"Invalid status values: {invalid_status.tolist()}")

    # 4. level must be in LevelENUM
    invalid_level = df.loc[~df["level"].isin([e.value for e in LevelENUM]), "level"]
    if not invalid_level.empty:
        raise ValueError(f"Invalid level values: {invalid_level.tolist()}")

    # 5. prereqs format check
    def check_prereqs(val):
        if pd.isna(val) or val == "":
            return True
        if not isinstance(val, str):
            return False
        groups = val.split("|")
        for g in groups:
            if not g.strip():
                return False
        return True

    invalid_prereqs = df.loc[~df["prereqs"].apply(check_prereqs), "prereqs"]
    if not invalid_prereqs.empty:
        raise ValueError(f"Invalid prereqs format: {invalid_prereqs.tolist()}")

    # 6. capstone, sophia avail, sophia intent, challenge avail, challenge intent: must be bool (0/1)
    bool_cols = ["capstone", "sophia avail", "sophia intent", "challenge avail", "challenge intent"]
    for col in bool_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise TypeError(f"'{col}' must be numeric (0/1)")
        if not df[col].dropna().isin([0, 1]).all():
            raise ValueError(f"'{col}' must only contain 0 or 1")

    # 7. session can be None or numeric
    if not df["session"].dropna().apply(lambda x: isinstance(x, (int, float))).all():
        raise TypeError("'session' must be None or a number")

    df = normalize_prereqs(df)


    print("DataFrame validation passed.")
    return True


BOOL_COLUMNS = ["capstone", "sophia avail", "sophia intent", "challenge avail", "challenge intent"]

def replace_bool(df: pd.DataFrame) -> pd.DataFrame:
    """Convert 0/NaN → False, 1 → True for boolean columns."""
    for col in BOOL_COLUMNS:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: True if x == 1 else False)
    return df



def get_excel():
    print("Fetching Excel")
    file_path = "/mnt/c/Users/clint/OneDrive/Documents/Education/DeVry/A-Scheduling/import_for_py.xlsx"

    # Load Excel file
    df = pd.read_excel(file_path)

    # Normalize columns 
    df = normalize_columns(df)

    # Validate and transform
    validate_df(df)

    # Apply transformations
    df = normalize_prereqs(df)
    df = replace_bool(df)

    print("Fetch/Validation Complete")
    return df

# endregion

# region Org

def parse_prereqs(prereq_str: str) -> list:
    """
    Convert a prereq string like 'AND1|AND2|[OR1|OR2|OR3]|AND3'
    into a structured list:
    ['AND1', 'AND2', ['OR1','OR2','OR3'], 'AND3']
    """
    if not prereq_str or str(prereq_str).lower() in {"none", "nan"}:
        return []

    tokens = prereq_str.split('|')
    structured = []

    for token in tokens:
        token = token.strip()
        if token.startswith('[') and token.endswith(']'):
            or_group = [pr.strip() for pr in token[1:-1].split('|')]
            structured.append(or_group)
        else:
            structured.append(token)
    return structured


def create_courses(df: pd.DataFrame) -> list:
    print("Creating Courses")
    courses = []

    for _, row in df.iterrows():
        c = Course(
            course_id=row["course id"],
            credit_hours=row["credit hours"],
            status=row["status"],
            level=row["level"],
            pre_reqs=parse_prereqs(row["prereqs"]),  # <-- structured prereqs here
            capstone=row["capstone"],
            session=row["session"],
            sophia_avail=row["sophia avail"],
            sophia_intent=row["sophia intent"],
            challenge_avail=row["challenge avail"],
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
        if c.level in LevelENUM:
            org_dict[c.level][c.course_id] = c
        else:
            err.append(c.course_id)

    if not err:
        print("Organization Complete")
        return org_dict
    
    raise ValueError(f"Courses Wrong Level||{err}")

def prioritize_courses(courses:dict, in_person: list = [])->list:
    """Prioritizes courses based on dependencies count and in_person list.
    Unaware; caution.
    Args:
        courses (dict): MUST be flattened: {course_id: course_obj,}
        in_person (list): List of course IDs to be prioritized.

    Returns:
        list: List of priority sorted Course objects [Highest...Lowest]
    """
    print("Prioritizing Courses...")
    # Get and flatten all prereqs
    p = []
    final_list = []
    for c in courses.values():
        items = []
        count = 0
        for req in c.pre_reqs:
            if isinstance(req,list):
                for i in req:
                    items.append(i)
            else:
                items.append(req)
            count += 1
        p.extend(items)
        # Get number of courses c is dependent on
        c.priority -= count
        final_list.append(c)

    # Add prereq counts to priority
    for i in p:
        c = courses.get(i)
        if c is not None:
            c.priority += 1

    # Sort by 'priority' in Course
    final_list.sort(reverse=True, key=lambda c: c.priority)
    print("Prioritizing Complete")

    return final_list

def filter_courses(courses: list) -> dict:
    """Filters courses into dict with CourseFilterENUM key and list of courses.
    Maintains list order of 'courses' arg.
    """
    print("Filtering Courses...")
    filtered_courses = {i: [] for i in FILT}

    for c in courses:
        if c.status == StatusENUM.COMPLETED or isinstance(c.session, int):
            filtered_courses[FILT.SET_SESSION].append(c)
        elif c.challenge_intent:
            if not c.challenge_avail:
                print(f"Intent but not avail || {c.course_id=}")
            else:
                filtered_courses[FILT.INTENT].append(c)
        elif c.sophia_intent:
            if not c.sophia_avail:
                print(f"Intent but not avail || {c.course_id=}")
            else:
                filtered_courses[FILT.INTENT].append(c)
        elif c.capstone:
            filtered_courses[FILT.CAPSTONE].append(c)
        else:
            filtered_courses[FILT.FREE].append(c)

    print("Filtering Complete")
    return filtered_courses

# endregion