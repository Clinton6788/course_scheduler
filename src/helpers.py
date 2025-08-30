

def prereq_total_count(prereq_str: str) -> int:
    """
    Count total number of prerequisite *requirements* in a prereq string:
    - Each AND prerequisite counts as 1
    - Each OR group (inside []) counts as 1
    """
    if not prereq_str or prereq_str.lower() in {"none", "nan"}:
        return 0  # No prereqs

    count = 0
    tokens = prereq_str.split('|')

    for token in tokens:
        token = token.strip()
        if token.startswith('[') and token.endswith(']'):
            # OR group counts as 1 requirement
            count += 1
        else:
            # AND prerequisite counts as 1 requirement
            count += 1

    return count

