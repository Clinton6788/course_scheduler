from dataclasses import dataclass, field
from src.user import User
from src.scheduling import Restraints, Session


@ dataclass
class TempSes:
    num: int
    grants: int
    course_count: int
    courses: list = field(default_factory=list)


def _over_benefits(
        cls, 
        user: User, 
        sessions: list[Session],
        tgt_list: list, 
        r: Restraints):
    

    # Get Max courses for Benefit Year

    # Get total remaining
    amnt = user.gib.active_benefit_year.amount

    # Get end date
    end_dt = user.gib.active_benefit_year.end

    # Get total Sessions:
    tot_ses = 0
    for s in sessions:
        tot_ses += 1 if s.start_date <= end_dt else 0

    # Get total coverage amount (GI Bill + Grants)
    tot_amnt = amnt + user.grants * tot_ses

def _adj_tgts(
        cls,
        tgt_list,
        min_course,
        max_course,
        index_low: int = None,
        index_high: int = None,
    ) -> tuple[bool,list]:
    """Readjusts target list, moving counts from inside 
    (index_low to index_high) to outside where possible. Defaults to moving to
    high side if all equal.

    Args:
        tgt_list (list): Full target list obtained from 
            cls._get_course_targets()
        min_course (int): Minimum courses per target. Pull from Restraints.
        max_course (int): Maximum courses per target. Pull from Restraints.
        index_low (int, Optional): Low end of index range to be adjusted.
        index_high (int, Optional): High end of index range to be adjusted.

    Returns:
        tuple (bool, list): Bool success of adjustment, adjusted list.
    """

    # Confirm a high or low index:
    if not (index_high or index_low):
        return (False, tgt_list)

    # Normalize non-values
    if index_high is None:
        index_high = len(tgt_list) -1
    if index_low is None:
        index_low = 0

    # Break into ranges
    low = tgt_list[:index_low]
    target = tgt_list[index_low:index_high +1]
    high = tgt_list[index_high +1:]

    # Helper to get total additional slots avail to add or remove
    def get_avail_movement(
            l: list, 
            f: str,
            min_c: int = min_course, 
            max_c: int = max_course, 
            ) -> int:
        """
        Args:
            l (list): Target list
            min_c (int): Minimum course count
            max_c (int): Max course count
            f (str): Function: "add" for total courses that can be added,
                "remove" for total courses that can be removed"
        """
        # Handle quick break first
        if len(l) == 0:
            return 0
        
        # Get course count for all
        count = 0
        for x in l:
            assert isinstance(x, int), f"All values in list must be 'int'. {l=}"
            count += x

        # Handle Adds -------------
        if f == "add":
            # Get max total courses
            m = len(l) * max_c

            return max(0, m - count)
        
        # Handle Removes ------------
        elif f =="remove":
            # Get min total courses
            m = len(l) * min_c

            return max(0, count - m)

        # Handle wrong input ------------
        else:
            raise ValueError(f"Arg 'f' must be 'add' or 'remove'. {f=}")
        
    # Get full potential movement:
    low_add = get_avail_movement(low, "add")
    high_add = get_avail_movement(high, "add")
    target_remove = get_avail_movement(target, "remove")

    # Break if not possible
    if (low_add < 1 and high_add < 1) or target_remove < 1:
        return (False, tgt_list)
    
    # Get highest index:
    t = max(target)
    i = target.index(t)
    v = target.pop(i)
    assert v > min_course, f"Error, value less than minimum: {v=}||{min_course=}"
    assert isinstance(v, int), f"Error, all tgt list must be int: {target=}" 

    # Subtract one, reinsert into target list
    v -= 1
    target.append(v)

    # Figure out which list is being added to; prioritize high slightly
    if low_add > high_add and low_add > 0:
        tgt = low
    elif high_add > 0:
        tgt = high
    else:
        raise ValueError(f"Cannot add to either\n{low_add=}||{high_add=}")

    # Get min index
    t = min(tgt)
    i = tgt.index(t)
    v = tgt.pop(i)
    assert v +1 <= max_course, f"Error, miscalculation\n {tgt_list=}\n {low=}\n {high=}"

    # Add one, reinsert and return
    v += 1
    tgt.append(v)

    # Concat, return
    modified = [*low, *target, *high]

    return (True, modified)