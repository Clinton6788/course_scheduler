import pandas as pd
from config.course_enums import StatusENUM, LevelENUM
from config.settings import (
    IN_PERSON_PRIORITY,
)
from pathlib import Path



# region Intake

# Mapping of possible column variations to standardized lowercase column names
COLUMN_MAP = {
    "course id": ["course id", "courseid", "course-id", "course_id", "id"],
    "credit hours": ["credit hours", "credithours", "credit-hours", "credit_hours", "ch", "chs"],
    "status": ["status"],
    "level": ["level"],
    "prereqs": ["prereqs", "pre-reqs", "pre_reqs"],
    "capstone": ["capstone"],
    "session": ["session"],
    "transfer intent": ["transfer intent", "transferintent", "transfer-intent", "transfer_intent"],
    "challenge intent": ["challenge intent", "challengeintent", "challenge-intent", "challenge_intent"],
}

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map any variant column names to standard lowercase names."""
    col_map = {}
    lower_cols = [col.lower().strip() for col in df.columns]

    for i, col in enumerate(lower_cols):
        for std_name, variants in COLUMN_MAP.items():
            if col in variants:
                col_map[df.columns[i]] = std_name
                break  # Stop at first match

    df = df.rename(columns=col_map)
    # Force all columns to lowercase and strip
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

def normalize_nan(df: pd.DataFrame | pd.Series, replacement_val = 0) -> None:
    """Removes pd.nan and replaces with replacement_val. OPERATES IN-PLACE.
    
    Args:
        df: Dataframe or Series to be normalized. CAUTION: ANY nan will be replaced; 
            recommend passing only desired series.
        replacement_val (any): Value to replace 'nan' with. Defaults to 0.
    """
    if isinstance(df, (pd.DataFrame, pd.Series)):
        df.fillna(replacement_val, inplace=True)
    else:
        raise TypeError("Input must be a pandas DataFrame or Series.")
    
    
def validate_df(df: pd.DataFrame) -> bool:
    """Validates that the DataFrame has required columns and correct formats."""
    print("Validating DataFrame")
    df = normalize_columns(df)

    required_columns = list(COLUMN_MAP.keys())

    # Check columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Credit hours must be int
    if not pd.api.types.is_integer_dtype(df["credit hours"]):
        raise TypeError("'credit hours' must be integers")

    # Status must be in StatusENUM. Empty is assumed "0" or statusenum.None
    invalid_status = df.loc[~df["status"].isin([e.value for e in StatusENUM]), "status"]
    if not invalid_status.empty:
        raise ValueError(f"Invalid status values: {invalid_status.tolist()}")

    # Level must be in LevelENUM
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

    # 6. capstone, transfer intent, challenge intent: must be bool
    bool_cols = ["capstone", "transfer intent", "challenge intent"]
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


BOOL_COLUMNS = ["capstone", "transfer intent", "challenge intent"]

def replace_bool(df: pd.DataFrame) -> pd.DataFrame:
    """Convert 0/NaN → False, 1 → True for boolean columns."""
    for col in BOOL_COLUMNS:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: True if x == 1 else False)
    return df


def fetch_data(file_path: str, is_absolute: bool = True) -> pd.DataFrame:
    """
    Loads an Excel or CSV file into a pandas DataFrame, normalizes and validates it, 
    and applies standard transformations.

    Args:
        file_path (str): Path to the Excel (.xlsx/.xls) or CSV (.csv) file.
        is_absolute (bool, optional): Whether `file_path` is absolute. Defaults to True.

    Returns:
        pd.DataFrame: Processed DataFrame with normalized columns, validated data, 
                      prerequisite transformations, and boolean replacements.

    Raises:
        ValueError: If the file extension is not supported OR if validation failed.
    """
    print("Fetching Excel or CSV")

    # Resolve path
    path = Path(file_path)
    if not is_absolute:
        path = Path.cwd() / path  # Treat as relative to current working dir

    # Determine file type
    ext = path.suffix.lower()

    # Load data accordingly
    if ext in [".xlsx", ".xls"]:
        df = pd.read_excel(path)
    elif ext == ".csv":
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")

    # Normalize column names
    df = normalize_columns(df)

    # Validate and transform
    valid = validate_df(df)
    if not valid:
        raise ValueError(f"File Validation Failed\n {df.head(10)}")
    df = normalize_prereqs(df)
    df = replace_bool(df)

    print("Fetch/Validation Complete")
    return df

# endregion


