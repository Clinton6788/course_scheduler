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