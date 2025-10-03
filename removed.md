Deleting copies; SHOULD be unnecessary
```python
    def _schedule_free(self, courses:dict, level):
        """Courses: {CourseFilterENUM: [Course,Course...],...}"""
        # Get approx CH cost
        ch_cost = self._get_ch_cost(level)

        # Init Temps, Copies
        free, capstone, intent, scheduled, sess_dict = self._get_copies(courses)

        def prereq_met(self, course, scheduled):



    def _get_copies(self, courses)->tuple:
        """Get copies of current structure for adjustments. Copies shallow;
        do NOT modify internal objects.
        Returns:
            tuple: [free_list, capstone_list, intent_list, scheduled_list, session_dict]
        """
        t = courses[CourseFilterENUM.FREE]
        free_copy = t.copy() # List of Courses
        t = courses[CourseFilterENUM.CAPSTONE]
        cap_copy = t.copy() # List of Courses
        t = courses[CourseFilterENUM.INTENT]
        int_copy = t.copy() # List of Courses

        scheduled_copy = self.scheduled.copy() # List of Courses
        temp_ses = self.sessions.copy() # Dict of {ses #: Session} Includes scheduled

        return free_copy, cap_copy, int_copy, scheduled_copy, temp_ses

```

```python
    # Step 1: Base priority modifications (count prereqs, capstone bonus/penalty)
    for c in courses.values():
        items = []
        count = 0
        for req in c.pre_reqs:
            if isinstance(req, list):
                items.extend(req)
            else:
                items.append(req)
            count += 1
        p.extend(items)

        c.priority -= count  # More prereqs = lower priority
        if c.capstone:
            c.priority -= 10  # Capstones lower priority baseline
        final_list.append(c)

    # Step 2: Add frequency-based influence
    for i in p:
        c = courses.get(i)
        if c is not None:
            c.priority += 1


    for c in final_list:
        c.priority += add_recursive_priority(c, courses)

    # Step 4: Sort
    final_list.sort(reverse=True, key=lambda c: c.priority)
    print("Prioritizing Complete")

```

```python
import pickle
from pathlib import Path
from src.intake import get_courses_pipeline

"""For laptop/no excel use"""
# def store_data():
#     course_dict = get_courses_pipeline([])

#     file_path = Path.cwd() / "course_dict.pkl"
#     with open(file_path, "wb") as f:
#         pickle.dump(course_dict, f)

# def load_data():
#     file_path = Path.cwd() / "course_dict.pkl"

#     # To load back:
#     with open(file_path, "rb") as f:
#         loaded_courses = pickle.load(f)
#     return loaded_courses
```

### First iteration of Scheduler

```python
from config.course_enums import (
    CourseFilterENUM as FilterENUM, 
    LevelENUM, 
    StatusENUM, 
    )
from src.scheduling.sessions import Session
import datetime as dt
from config.settings import (
    COST_PER_CH_GRAD,
    COST_PER_CH_UNDERGRAD,
    COST_PER_COURSE,
    COST_PER_SESSION,
    ALUMNI_SAVINGS_PERCENT,
    )
import pandas as pd
from src.scheduling.course import Course

class Scheduler:
    def __init__(self):
        self.sessions = {}
        self.scheduled = []
        self.avail_ses = [] # Session Objects
        self.ses_funds = 0 # Ideal max cost of session; is not absoloute
        self.finmgr = FinanceMGR # Do not init yet; init in schedule courses

    def schedule_courses(
            self, 
            courses:dict, 
            restraints: dict,
            inperson: list = [], 
            ):
        """
        Main point of entry for scheduling courses. Schedules courses based on the provided level and options.
        
        Args:
            courses (dict): Dictionary of courses categorized by type or filter. 
                            Example: {LevelEnum: {FilterENUM: [Courses,...]}}
            restraints (dict): Dictionary of restraints for scheduling. Keys in RestraintsENUM.
            inperson (list, optional): List of course IDs to prioritize or enforce (based on 'must_have_inperson).
        
        Returns:
            dict: Scheduled courses with course IDs as keys and scheduled details as values.
        
        Notes:
            - This function handles prerequisite checks and in-person constraints.
            - Must_have_inperson=True ensures in-person requirement is respected; fails if not able to schedule
        """
        print("Scheduling...")

        # Verify Data
        self._verify_course_dict(courses)
        print("Verification Passed")

        # Prep avail sessions (Sessions that the program will see as "free")
        for k,v in SESSIONS.items():
            if v >= dt.date.today():
                self.avail_ses.append(Session(k))
                # print(f"Available Sessions: {self.avail_ses}")

        # Get easily workable structures
        working_courses = []
        for lev, filtered_dict in courses.items():
            working_courses.append((lev, filtered_dict))
        # print(f"Working Courses: {working_courses}")

        # Assign fixed to sessions (completed, inprogress, set)
        self._assign_fixed(working_courses)
        print(f"Assigned: {self.scheduled}")

        # Init and pre-load finmgr with historical sessions (started on/before today)
        today = dt.date.today()
        sess_list = []
        for ses in self.sessions.values():
            if ses.start_date <= today:
                sess_list.append(ses)

        self.finmgr(sess_list)


        # Assign Remainder
        self._assign_free(working_courses, restraints, inperson)


    def _assign_free(self, working_courses: list[tuple], restraints, inperson):
        """Assigns Courses by priority and restraints.
        """
        print("Assigning Free Courses...")

        for t in working_courses:
            level, filtered_dict = t

            # Get base level course lists
            free = filtered_dict.get(FilterENUM.FREE, [])
            intent = filtered_dict.get(FilterENUM.INTENT, [])
            capstone = filtered_dict.get(FilterENUM.CAPSTONE, [])

            # Check for quick cut:
            if not free and not intent and not capstone:
                return
            
            # Consider intended classes as completed for prereq
            self.scheduled.extend(intent)
            
            # Get copies for working
            sess_copy = self.sessions.copy()
            scheduled_copy = self.scheduled.copy()
            avail_sess_copy = self.avail_ses.copy()
            avail_sess_copy.sort()

            copies = {
                'sessions':sess_copy,
                'scheduled':scheduled_copy,
                'avail_sess':avail_sess_copy
            }


            # Consolidate into single, sorted list
            courses = []
            courses.extend(free)
            courses.extend(capstone) # Priority already adjusted
            courses.sort(key= lambda c: c.priority)

            self._schedule_sessions(courses, level, restraints, inperson, copies)


    def _schedule_sessions(self, courses:list[Course], level:int, restraints:dict, inperson:list, sch:dict):
        """Attempts to schedule all sessions; """
        # Flatten Schedule Copies
        sessions = sch.get('sessions')
        scheduled = sch.get('scheduled')
        avail_sess = sch.get('avail_sess')
        
        # Handle in person
        sat = []
        if isinstance(inperson, list) and inperson != []:
            inperson_courses = [c for c in courses if c.course_id in inperson]
            # If unsatisfied prereq, skip course
            for c in inperson_courses:
                unsat = self.unsatisfied_prereqs(c, scheduled)
                if unsat == []:
                    sat.append(c)
            
        # Verify Restraint:
        if restraints.get(RestraintsENUM.FIRST_SES_INPERSON) and sat == []:
            raise RuntimeError(f"Unable to satisfy In Person Requirement!")
        

        # Re sort List
        courses.sort(key=lambda c: c.priority, reverse=True)

        # Iter through and create sessions
        max_course = restraints.get(RestraintsENUM.SES_MAX_CLASS)
        while len(courses) > 0:
            # Remove active session for working
            mt_ses = avail_sess.pop(0)
            mt_ses.level = level
            ses = self._create_session(mt_ses, sat, courses, scheduled, max_course)
            # Confirm restraints
            if not self._is_valid_session(ses, restraints):
                raise RuntimeError(f"Invalid Session||{ses}")
            
            # print(f"STATUS: Session={ses}\nSession Has={[c for c in ses.courses]}\n"
            #       f"Current Courses= {courses}")
            # Move assigned courses
            for c in ses.courses:
                # print("Course: ", c)
                # print("COURSES: ", len(courses))
                # for i in courses:
                #     print(c.course_id)
                # courses.remove(c)
                scheduled.append(c)

            # Update sessions
            sessions[ses.num] = ses

        # Session creation complete; commit and return
        self.sessions = sessions
        self.scheduled = scheduled
        self.avail_ses = avail_sess
                
            

    def _create_session( # Done
            self, 
            ses:Session, 
            inperson_sat:list[Course], 
            courses:list[Course], 
            scheduled:list[Course],
            max_course:int)->Session: 
        
        inperson = False
        ic = 0 # Courses iterations
        ip = 0 # Inperson iterations
        t = len(inperson_sat) + len(courses) # Total allowed
        i = 0 # Total iterations
        while len(ses.courses) < max_course and len(courses) > 0:
            # Fail early
            if i > t:
                raise RuntimeError(f"Failed to schedule session||{ses}||{courses=}")
            
            # Prioritize inperson, but only one per
            if not inperson and ip < len(inperson_sat):
                p = True
                c = inperson[ip]

            else:
                p = False
                if not p and ic >= len(courses):
                    raise RuntimeError(f"Failed to schedule session||{ses}||{courses=}")
                c = courses[ic]

            # Attempt to slot course:
            if self.unsatisfied_prereqs(c, scheduled) == []:
                # Prereqs satisfied, schedule, remove and resest iters
                if not c in ses.courses:
                    ses.add_course(c)
                    if p:
                        inperson = True

                if c in inperson_sat:
                    inperson_sat.remove(c)
                if c in courses:
                    courses.remove(c)
                ic = 0
                ip = 0
                i = 0
            
            # Failed to slot: 
            # TODO: Update handling to get prereqs? 
            # should be nullified by the sort unless inperson
            else:
                if p:
                    ip += 1
                else:
                    ic += 1
                i += 1

        return ses

        
    def _is_valid_session(self, session:Session, restraints: dict)->bool:
        """Check and enforce restraints. 
        Args:
            session (Session): 
            restraints (dict): Restraints to be enforced. Keys must be RestraintsENUM.
        Returns:
            bool
        """
        return True


    def _is_valid_schedule(self, sessions: list[Session], restraints: dict)->tuple:
        """Check and enforce restraints. 
        Args:
            sessions (list): Full, tentative list of sessions to confirm
            restraints (dict): Restraints to be enforced. Keys must be RestraintsENUM.
        Returns:
            tuple: (bool, Session|None, str|None) -> (is_valid, session with error, error type)
        """
        pass


    def _get_copies(self, courses:dict)->dict: # Done
        """Get copies of current structure for adjustments. Copies shallow;
        any object modification affects all.
        Args:
            courses (dict): Flattened 'filtered courses' {FilterENUM: [Courses]}
        Returns:
            dict: Same format as passed; just copies of all
        """
        copy_dict = {}
        for k, v in courses.items():
            copy_dict[k] = v.copy()

        return copy_dict

    def _assign_fixed(self, working_courses)->None: # Done
        """Assigns completed, fixed and in-progress courses to self.scheduled;
        Adds session objects to self.sessions{}.
        """
        print("Scheduling Fixed Courses...")
        for t in working_courses:
            level, courses = t
            fixed = courses.get(FilterENUM.SET_SESSION, None)
            print(f"FIXED: {fixed}")

            if fixed is None:
                continue

            for c in fixed:
                # Handle transfers
                if not c.session or pd.isna(c.session):
                    if not c.status == StatusENUM.COMPLETED:
                        raise RuntimeError(f"Assign Fixed||Improper Filtering||{c}")
                    self.scheduled.append(c)
                    continue

                # Handle Set Session
                ses = self.sessions.get(c.session, None)
                if ses is None: # Create new Session
                    ses = Session(c.session)
                    ses.level = level
                    ses.add_course(c)
                    self.sessions[c.session] = ses
                else:
                    if ses.level is not level:
                        raise RuntimeError(f"ERROR||Assign Fixed||{ses.level=}||{level=}")
                    ses.add_course(c)
                self.scheduled.append(c)
        print("Fixed Courses Scheduled")

    def _verify_course_dict(self, courses): # Done
        # Basic verification; brute force
        msg = f"Scheduler||Improper Courses||{courses}"
        assert isinstance(courses, dict), msg

        normalized = {}
        for lvl, subdict in courses.items():
            assert isinstance(lvl, int), msg
            assert isinstance(subdict, dict), msg
            for k, v in subdict.items():
                assert isinstance(k, int), msg
                assert isinstance(v, list), msg
                for c in v:
                    assert isinstance(c, Course), msg

    def unsatisfied_prereqs(self, course, completed: list = None):
        """
        Returns a list of unsatisfied prerequisites:
        - AND prerequisites as strings
        - OR groups as lists if none are satisfied
        """
        if completed is None:
            completed = self.scheduled

        unsatisfied = []

        for pre in course.pre_reqs:
            if isinstance(pre, list):  # OR group
                if not any(p in completed for p in pre):
                    unsatisfied.append(pre)  # Include the whole group
            else:  # AND prerequisite
                if pre not in completed:
                    unsatisfied.append(pre)

        return unsatisfied


    def _calc_ses_funds(self):
        self.ses_funds = round(
            GRANT_PELL + GRANT_OPP +
            (GI_BILL/(SESSIONS_PER_SEMESTER*SEMESTERS_PER_YEAR))
            ,0
        )

    def _get_ch_cost(self, level)-> int:
        """Gets average credit hour cost. Assumes MAX course load."""
        if level == LevelENUM.UNDERGRAD:
            ch_rate = COST_PER_CH_UNDERGRAD
            m = 1
        elif level == LevelENUM.GRADUATE:
            ch_rate = COST_PER_CH_GRAD
            m = (100 - ALUMNI_SAVINGS_PERCENT)/100
        else:
            raise ValueError(f"Get CH Cost||Improper {level=}")
        
        # Assume average of 3 credit hours
        avg_ch = 3
        total_ch = MAX_COURSE_PER_SESSION * avg_ch

        ch_cost = total_ch * ch_rate * m
        fee_cost = MAX_COURSE_PER_SESSION * COST_PER_COURSE + COST_PER_SESSION

        total_cost = ch_cost + fee_cost
        return total_cost / total_ch        

```

### Scheduler method that was redundant

```python
    @classmethod
    def _plan_session_levels(
        cls,
        user: User, 
        restraints: Restraints, 
        spread_between: Optional[int] = None
        ) -> None:
        """
        Assigns level to sessions in user.free_sessions after session creation AND set courses scheduled.

        Args:
            user (User): User instance with free_sessions created.
            restraints (Restraints): Scheduling constraints.
            spread_between (int, optional): If provided, will spread across a fixed number of sessions.
        """
        r = restraints
        under_count = sum(1 for c in user.courses if c.level == LevelENUM.UNDERGRAD and not c.session)
        grad_count = sum(1 for c in user.courses if c.level == LevelENUM.GRADUATE and not c.session)
        total_courses = under_count + grad_count

        if total_courses == 0:
            return  # No levels to assign

        # Determine session count
        if spread_between and spread_between > 0:
            total_sessions = spread_between
        else:
            under_ses = (under_count + r.ses_min_class - 1) // r.ses_max_class
            grad_ses = (grad_count + r.ses_min_class - 1) // r.ses_max_class
            total_sessions = under_ses + grad_ses

        # Limit by GI Bill
        if hasattr(user, "gib") and user.gib and not r.exceed_benefits:
            session_days = SESSION_WEEKS * 7
            max_sessions = user.gib.get_remaining_days() // session_days
            total_sessions = min(total_sessions, max_sessions)

        # Get actual sessions to plan
        sessions = [s for s in user.free_sessions if s.start_date >= dt.date.today()]
        if total_sessions < len(sessions):
            sessions = sessions[:total_sessions]

        # Compute session counts by level
        under_ratio = under_count / total_courses if total_courses else 0
        grad_ratio = grad_count / total_courses if total_courses else 0

        under_ses = round(total_sessions * under_ratio)
        grad_ses = total_sessions - under_ses

        # Assign levels to sessions
        print("_____________PLAN SESSION LEVELS_____________")
        for i, s in enumerate(sessions):
            s.level = LevelENUM.UNDERGRAD if i < under_ses else LevelENUM.GRADUATE
            print(f"\n {s.num}: {s.level}")

```