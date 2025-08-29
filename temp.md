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
