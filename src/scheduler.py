from course_enums import CourseFilterENUM, LevelENUM
from src.sessions import Session
import datetime as dt
from settings import (
    SESSIONS,
    MAX_COURSE_PER_SESSION,
    GRANT_OPP,
    GRANT_PELL,
    GI_BILL,
    SEMESTERS_PER_YEAR,
    SESSIONS_PER_SEMESTER,
    COST_PER_CH_GRAD,
    COST_PER_CH_UNDERGRAD,
    COST_PER_COURSE,
    COST_PER_SESSION,
    ALUMNI_SAVINGS_PERCENT,
    MAX_RECURSION
    )
import pandas as pd
from src.courses import Course

class Scheduler:
    def __init__(self):
        self.sessions = {}
        self.scheduled = []
        self.avail_ses = [] # Session Number Only
        self.ses_funds = 0 # Ideal max cost of session; is not absoloute

    def schedule_courses(
            self, 
            courses:dict, 
            in_person: list = [], 
            must_have_inperson: bool = False,
            ):
        """
        Main point of entry for scheduling courses. Schedules courses based on the provided level and options.
        
        Args:
            courses (dict): Dictionary of courses categorized by type or filter. 
                            Example: {LevelEnum: {FilterENUM: [Courses,...]}}
            in_person (list, optional): List of course IDs to prioritize or enforce (based on 'must_have_in_person).
            must_have_inperson (bool, optional): If True, fails if unable to schedule in-person on first avail session. Default False.
        
        Returns:
            dict: Scheduled courses with course IDs as keys and scheduled details as values.
        
        Notes:
            - This function handles prerequisite checks and in-person constraints.
            - Must_have_inperson=True ensures in-person requirement is respected; fails if not able to schedule
        """
        # Verify Data
        self._verify_course_dict(courses)
        print("Verification Passed")





    def _verify_course_dict(self, courses):
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

    def _schedule_free(self, courses:dict, level, recur = 0):
        """Courses: {CourseFilterENUM: [Course,Course...],...}"""
        # Get approx CH cost
        ch_cost = self._get_ch_cost(level)

        # Init Temps, Copies
        free, capstone, intent, scheduled, ses_dict = self._get_copies(courses)
        scheduled.extend(intent)
        temp_courses = {
            'free':free,
            'cap': capstone,
            'intent':intent,
            'scheduled':scheduled,
            'sess_dict':ses_dict
        }

        count = 0
        tot = len(temp_courses['free']) # Assumes 1 iter per course; more than enough
        while count < tot:
            print(f"Scheduling Session||{count}")
            new = self._schedule_temp_session(temp_courses)
            if new == False:
                raise RecursionError(temp_courses) # HEAVY raise; try to diagnose;
            temp_courses = new
            count += 1


    def _schedule_temp_session(
            self, 
            temp_courses: dict,
            recur = 0):
        
        if recur >= MAX_RECURSION:
            return False
        
        free = temp_courses['free'].copy()
        cap = temp_courses['cap'].copy()
        intent = temp_courses['intent'].copy()
        scheduled = temp_courses['scheduled'].copy()
        sess_dict = temp_courses['sess_dict'].copy()
        
        temp_ses_group = []
        count = 0
        while len(temp_ses_group)<MAX_COURSE_PER_SESSION and count < MAX_RECURSION:
            count += 1
            if len(free) == 0:
                break
            c = free[0]
            # unsatisfied prereq
            u = self.unsatisfied_prereqs(c, scheduled)
            # Free for scheduling
            if not u:
                free.pop(0)
                temp_ses_group.append(c)
                continue
            else:
                # Unsatisfied Prereq
                req_list = []
                for pre in u:
                    if isinstance(pre,list):
                        key = next((k for k in pre if k in free),None)
                        if key is None:
                            raise RuntimeError(f"Unknown Requirement||{pre}||{c}")
                        req_list.append(key)
                    else:
                        req_list.append(pre)
                
                # Bump PreReq Priority by 'x'
                for p in req_list:
                    x = (c.priority - p.priority) + recur
                    p.priority += x

                self._schedule_temp_session(temp_courses, recur+1)

        if len(temp_ses_group) < MAX_COURSE_PER_SESSION and len(free)>=1:
            # Recursion Error
            raise RecursionError(f"Temp Session||{temp_courses}")
        
        return temp_ses_group
        



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

    def _schedule_fixed(self, fixed: list, level: int):
        print("Scheduling Fixed Courses...")
        for c, i in enumerate(fixed):
            ses = self.sessions.get(c.session, None)
            if ses is None:
                ses = Session(c.session, level, [c])
                self.sessions[c.session] = ses
            else:
                if ses.level is not level:
                    raise RuntimeError(f"ERROR||Schedule Fixed||{ses.level=}||{level=}")
                ses.add_course(c)
            self.scheduled.append(c)
            fixed.pop(i)

        print("Fixed Courses Scheduled")

    def _calc_ses_funds(self):
        self.ses_funds = round(
            GRANT_PELL + GRANT_OPP +
            (GI_BILL/SESSIONS_PER_SEMESTER*SEMESTERS_PER_YEAR)
            ,0
        )

    def _get_ch_cost(self, level)-> int:
        """Assumes MAX course load."""
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
