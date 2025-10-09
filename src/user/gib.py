import datetime as dt
from dataclasses import dataclass
from dateutil.relativedelta import relativedelta
from typing import Optional

from src.scheduling import Session  # Assumed import paths
# from src.user import User  # You can add later if needed for user-level association


@dataclass
class BenefitYear:
    st: dt.date
    end: dt.date
    amount: float


class GIB:
    def __init__(
        self,
        yearly_amount: int | float,
        start_dt: tuple[int, int],
        remaining_time: tuple[int, int],
        days_as_of: dt.date,
    ):
        """
        Args:
            yearly_amount (int | float): Yearly amount of financial coverage.
            start_dt (tuple): (month, day) of the benefit cycle start.
            remaining_time (tuple): (months, days) of benefit time remaining.
            days_as_of (dt.date): Date the remaining time was calculated from.
        """
        start_date = dt.date(dt.date.today().year, *start_dt)
        end_date = start_date + relativedelta(years=1) - dt.timedelta(days=1)

        self.yearly_amount = yearly_amount
        self.benefit_start = start_date
        self.active_benefit_year = BenefitYear(start_date, end_date, yearly_amount)

        self.benefit_years: dict[dt.date, BenefitYear] = {
            start_date: self.active_benefit_year
        }

        m, d = remaining_time
        self.remaining_days = m * 30 + d
        self.asof = days_as_of

        # Track charged Sessions
        self.charged_sessions = []

    # Must be called upon INIT and changes
    def charge_historical(self, sessions: list[Session]) -> None:
        """
        Applies completed or in-progress sessions to update initial GI Bill usage.
        Should be run once per user when loading from saved data or course changes.
        """
        for s in sessions:
            if s in self.charged_sessions:
                continue
            was_covered = self._charge_days(s, final=True)
            self._charge_cost(s, was_covered, final=True)

    def charge_session(self, sess: Session, final: bool = False) -> tuple[bool, float]:
        """
        Charge a single session to GI Bill benefits or simulate the impact.

        Returns:
            (ses covered, total charge to user)
        """
        assert isinstance(sess, Session), f"Invalid session: {type(sess)}"

        if sess.num in self.charged_sessions:
            print(f"Already charged session {sess.num}")
            return
        
        # Must charge days first to ensure cost is charged fully if no benefits
        ses_covered = self._charge_days(sess, final)
        charge_amount, coverage = self._charge_cost(sess, ses_covered, final)

        if final:
            self.charged_sessions.append(sess.num)
            # Add total amount of coverage to session
            sess.add_gib(coverage)
            # Add current remaining Benefits
            sess.gib_remaining = self.active_benefit_year.amount


        return ses_covered, charge_amount

    def _charge_days(self, session: Session, final: bool) -> bool:
        """
        Determines if GI Bill can cover the given session and optionally charges for it.

        A session is fully covered if the user has at least one day of benefits remaining 
        on the session's start date.

        Args:
            session (Session): The session to charge.
            final (bool): If True, apply the deduction permanently.

        Returns:
            bool: True if the session is covered by GI Bill benefits, False otherwise.
        """
        # If no benefit days left on the session's start date, not covered
        if self.remaining_days <= 0 or session.start_date < self.asof:
            return False

        # If at least one day left on session start, full session is covered
        session_duration = (session.end_date - session.start_date).days
        updated_remaining = self.remaining_days - session_duration

        if final:
            self.remaining_days = updated_remaining

        return True
    
    def _charge_cost(self, session: Session, was_covered: bool, final: bool) -> tuple:
        """
        Deducts the session cost from the appropriate benefit year.

        Args:
            session (Session): The session to charge.
            was_covered (bool): If True, attempt to cover with GI Bill.
            final (bool): If True, apply the deduction permanently.

        Returns:
            float: Amount the user must pay (0 if fully covered).
        """
        ses_date = session.start_date
        ses_cost = session.adj_cost

        if not was_covered:
            return ses_cost

        # Determine the benefit year for this session
        year_start = dt.date(ses_date.year, self.benefit_start.month, self.benefit_start.day)
        if ses_date < year_start:
            year_start = year_start.replace(year=year_start.year - 1)

        year_end = year_start + relativedelta(years=1) - dt.timedelta(days=1)

        # Use working copy if not final
        target_years = self.benefit_years if final else {
            k: BenefitYear(v.st, v.end, v.amount) for k, v in self.benefit_years.items()
        }

        # Initialize year if missing
        if year_start not in target_years:
            target_years[year_start] = BenefitYear(year_start, year_end, self.yearly_amount)

        # Apply coverage
        year = target_years[year_start]
        coverage = min(ses_cost, year.amount)
        year.amount -= coverage
        user_owes = ses_cost - coverage

        # Apply updated copy if final
        if final is False:
            return user_owes
        else:
            self.benefit_years = target_years
            return user_owes, coverage



    def get_total_remaining(self, year) -> float:
        by = self.benefit_years.get(year, None)
        return by.amount if by else by

    def get_remaining_days(self) -> int:
        return self.remaining_days

