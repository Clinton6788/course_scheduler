

def generate_tgt_lists(
        course_dict, 
        max_sessions=None,
        ses_min_course=2,
        ses_max_course=4,
        ) -> list[list[int]]:
    """
    Generate all valid globally front-heavy session-course distributions for the
    given course levels.

    Each entry in `course_dict` represents one course level and the total number
    of courses that must be allocated for that level. Levels are scheduled
    independently, but their resulting session-course allocations are combined
    into a single global target list.

    A valid distribution for a level:
        • Uses any number of sessions ≥ 1.
        • Assigns `ses_min_course` to `ses_max_course` courses per session.
        • Cannot have a final session with fewer than `ses_min_course` courses.
        • Must sum exactly to the total course count for that level.
        • Is internally front-loaded (earlier sessions have equal or larger
          loads than later ones).

    After per-level patterns are generated:
        1. One valid pattern is chosen for each level (Cartesian product).
        2. All session counts from all levels are merged.
        3. The merged list is sorted in descending order (global front-loading).
        4. If `max_sessions` is provided, merged lists longer than that value
           are discarded.
        5. Duplicate global lists (arising from different internal combinations)
           are removed.
        6. Final results are sorted in descending lexicographic order so the
           most heavily front-loaded distributions appear first.

    Args:
        course_dict (dict[int, int]):
            Mapping of course level → total number of courses in that level.
        max_sessions (int | None):
            Maximum allowed number of sessions for the final combined list.
            If None, no upper limit is applied.
        ses_min_course (int):
            Minimum number of courses allowed in any session.
        ses_max_course (int):
            Maximum number of courses allowed in any session.

    Returns:
        list[list[int]]:
            A list of globally front-heavy session-course distributions, each
            distribution being a list of integers representing course counts per
            session.

    Notes:
        • No mixing of course levels occurs during allocation—mixing only occurs
          after valid per-level patterns are produced.
        • Results are deterministic and sorted from most to least front-heavy.
        • If any level has zero valid patterns, the function returns an empty
          list.
    """

    # ---------- helper: generate all patterns for a single level ----------
    def generate_level_patterns(total_courses: int, max_ses: int):
        results = []

        for ses in range(1, max_ses + 1):
            def backtrack(i, remaining, cur):
                if i == ses:
                    if remaining == 0:
                        results.append(cur.copy())
                    return

                # last session must match remainder
                if i == ses - 1:
                    if ses_min_course <= remaining <= ses_max_course:
                        cur.append(remaining)
                        backtrack(i + 1, 0, cur)
                        cur.pop()
                    return

                # try values from MAX → MIN (front-heavy)
                for c in range(ses_max_course, ses_min_course - 1, -1):
                    if c > remaining:
                        continue
                    rem = remaining - c

                    # feasibility check
                    min_possible = (ses - i - 1) * ses_min_course
                    max_possible = (ses - i - 1) * ses_max_course
                    if not (min_possible <= rem <= max_possible):
                        continue

                    cur.append(c)
                    backtrack(i + 1, rem, cur)
                    cur.pop()

            backtrack(0, total_courses, [])

        return results

    # ---------- generate patterns per level ----------
    level_patterns = []
    for lvl, total in course_dict.items():
        computed_max = (total + ses_min_course - 1) // ses_min_course
        allowed_max = max_sessions or computed_max
        pats = generate_level_patterns(total, allowed_max)
        if not pats:
            return []  # no valid patterns → immediate failure
        level_patterns.append(pats)

    # ---------- combine levels ----------
    from itertools import product

    combined = []
    for combo in product(*level_patterns):
        # flatten patterns from each level
        flat = [x for pat in combo for x in pat]

        # globally front-load sessions
        flat_sorted = sorted(flat, reverse=True)

        # enforce max sessions
        if max_sessions is None or len(flat_sorted) <= max_sessions:
            combined.append(flat_sorted)

    # ---------- remove duplicates & globally order front-heavy ----------
    # duplicates occur because different internal combinations
    # can produce the same globally sorted list
    unique = []
    seen = set()
    for lst in combined:
        tup = tuple(lst)
        if tup not in seen:
            seen.add(tup)
            unique.append(lst)

    # sort by strongest front-loading:
    # compare lexicographically (descending)
    unique.sort(reverse=True)

    return unique





