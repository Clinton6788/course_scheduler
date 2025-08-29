from course_enums import CourseFilterENUM as FilterENUM, LevelENUM, StatusENUM, RestraintsENUM
from src.sessions import Session
import datetime as dt
from settings import (
    SESSIONS,
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
from src.finances import FinanceMGR

class Scheduler:
    def __init__(self):
        self.sessions = {}
        self.scheduled = []
        self.avail_ses = [] # Session Number Only
        self.ses_funds = 0 # Ideal max cost of session; is not absoloute
        self.finmgr = FinanceMGR # Do not init yet

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

        # Prep avail sessions
        for k,v in SESSIONS.items():
            if v >= dt.date.today():
                self.avail_ses.append(k)

        # Get easily workable structures
        working_courses = []
        for lev, filtered_dict in courses.items():
            working_courses.append((lev, filtered_dict))

        # Assign completed or in progress
        self._assign_fixed(working_courses)

        # Init and pre-load finmgr with historical sessions NOT ALL SET
        today = dt.date.today()
        sess_list = []
        for ses in self.sessions.values():
            if ses.start_date <= today:
                sess_list.append(ses)

        self.finmgr(sess_list)


        # Assign Remainder
        self._assign_free(working_courses, restraints, inperson)


    def _assign_free(self, working_courses, restraints, inperson):
        """Assigns Courses by priority and restraints.
        """
        print("Assigning Free Courses...")
        # Get copies for working
        sess_copy = self.sessions.copy()
        scheduled_copy = self.scheduled.copy()
        avail_sess_copy = self.avail_ses.copy()

        working_copies = []
        for level, filtered_courses in working_courses:
            working_copies.append((level, self._get_copies(filtered_courses)))

        copies = {
            'sessions': sess_copy,
            'scheduled': scheduled_copy,
            'avail_sessions': avail_sess_copy,
            'working_courses': working_copies
        }

        # Attempt to schedule sessions
        # MAY be incomplete; verify or handle with ignorance
        tentative = self._schedule_sessions(copies, restraints, inperson)

    def _schedule_sessions(self, copies, restraints, inperson, recur = 0):
        """Attempts to schedule all sessions; """
        print(f"Schduling attempt {recur}")
        if recur >= MAX_RECURSION:
            return copies
        
        # we make copies of copies and 
        # try to schedule single session at a time



        # on success, local commit, recurse

        # on failure, recurse

        pass
        


    def _is_valid_schedule(self, sessions: dict, restraints: dict)->bool:
        """Check and enforce restraints. 
        Args:
            sessions (dict): Full, tentative dict of changes to enforce restraints on.
            restraints (dict): Restraints to be enforced. Keys must be RestraintsENUM.
        """
        for k, ses in sessions:


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
                    ses = Session(c.session, level, [c])
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
