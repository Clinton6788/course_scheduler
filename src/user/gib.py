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
            self._charge_days(s, final=True)
            self._charge_cost(s, final=True)

    def charge_session(self, sess: Session, final: bool = False) -> tuple[int, float]:
        """
        Charge a single session to GI Bill benefits or simulate the impact.

        Returns:
            (remaining_days, total_remaining_amount)
        """
        assert isinstance(sess, Session), f"Invalid session: {type(sess)}"

        if sess.num in self.charged_sessions:
            print(f"Already charged session {sess.num}")
            return
        
        days_remaining = self._charge_days(sess, final)
        amount_remaining = self._charge_cost(sess, final)

        if final:
            self.charged_sessions.append(sess.num)

        return days_remaining, amount_remaining

    def _charge_days(self, session: Session, final: bool) -> int:
        """
        Charges GI Bill days for a single session if it ends on or after `self.asof`.

        Args:
            session (Session): The session to charge.
            final (bool): If True, apply the deduction permanently.

        Returns:
            int: Remaining benefit days after the charge.
        """
        if session.end_date < self.asof:
            return self.remaining_days

        used = (session.end_date - session.start_date).days
        remaining = self.remaining_days - used

        if final:
            self.remaining_days = remaining

        return remaining
    
    def _charge_cost(self, session: Session, final: bool) -> float:
        """
        Deducts the session cost from the appropriate benefit year.

        Args:
            session (Session): The session to charge.
            final (bool): If True, apply the deduction permanently.

        Returns:
            float: Amount used from the applicable benefit year.
        """
        ses_date = session.start_date
        ses_cost = session.tot_cost

        # Determine the benefit year start
        year_start = dt.date(ses_date.year, self.benefit_start.month, self.benefit_start.day)
        if ses_date < year_start:
            year_start = year_start.replace(year=year_start.year - 1)

        year_end = year_start + relativedelta(years=1) - dt.timedelta(days=1)

        # Work on a copy to avoid mutating original unless final
        benefit_years_copy = {
            k: BenefitYear(v.st, v.end, v.amount) for k, v in self.benefit_years.items()
        }

        # Initialize year if missing
        if year_start not in benefit_years_copy:
            benefit_years_copy[year_start] = BenefitYear(year_start, year_end, self.yearly_amount)

        # Deduct and calculate amount used
        year = benefit_years_copy[year_start]
        prev_amount = year.amount
        year.amount -= ses_cost
        used = prev_amount - year.amount

        if final:
            self.benefit_years = benefit_years_copy

        return used



    def get_total_remaining(self, year) -> float:
        by = self.benefit_years.get(year, None)
        return by.amount if by else by

    def get_remaining_days(self) -> int:
        return self.remaining_days

