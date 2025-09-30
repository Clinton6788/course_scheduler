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

        self._init_calculation = False

    # Must be called upon INIT
    def charge_historical(self, sessions: list[Session]) -> None:
        """
        Applies completed or in-progress sessions to update initial GI Bill usage.
        Should be run once per user when loading from saved data.
        """
        if self._init_calculation:
            return

        self._charge_days(sessions, final=True)
        self._charge_cost(sessions, final=True)
        self._init_calculation = True

    # -----------------------------
    # ✅ Public Charge Method
    # -----------------------------
    def charge_session(self, sess: Session, final: bool = False) -> tuple[int, float]:
        """
        Charge a single session to GI Bill benefits or simulate the impact.

        Returns:
            (remaining_days, total_remaining_amount)
        """
        assert isinstance(sess, Session), f"Invalid session: {type(sess)}"
        days_remaining = self._charge_days([sess], final)
        amount_remaining = self._charge_cost([sess], final)
        return days_remaining, amount_remaining

    # -----------------------------
    # 🧠 Internal: Days
    # -----------------------------
    def _charge_days(self, sessions: list[Session], final: bool) -> int:
        """
        Charges 56 days for each session after `self.asof`.

        Returns:
            int: remaining days
        """
        used = 0
        for ses in sessions:
            if ses.end_date >= self.asof:
                used += 56  # Full session charge

        remaining = self.remaining_days - used
        if final:
            self.remaining_days = remaining
        return remaining

    # -----------------------------
    # 🧠 Internal: Cost
    # -----------------------------
    def _charge_cost(self, sessions: list[Session], final: bool) -> float:
        """
        Deducts cost of sessions from the proper benefit year.

        Returns:
            float: total remaining across all years
        """
        benefit_years_copy = {
            k: BenefitYear(v.st, v.end, v.amount) for k, v in self.benefit_years.items()
        }

        for ses in sessions:
            ses_date = ses.start_date
            ses_cost = ses.tot_cost

            # Determine benefit year
            year_start = dt.date(ses_date.year, self.benefit_start.month, self.benefit_start.day)
            if ses_date < year_start:
                year_start = year_start.replace(year=year_start.year - 1)

            year_end = year_start + relativedelta(years=1) - dt.timedelta(days=1)

            if year_start not in benefit_years_copy:
                benefit_years_copy[year_start] = BenefitYear(year_start, year_end, self.yearly_amount)

            benefit_years_copy[year_start].amount -= ses_cost

        if final:
            self.benefit_years = benefit_years_copy

        return sum(by.amount for by in benefit_years_copy.values())

    # -----------------------------
    # 📦 Optional: Export State
    # -----------------------------
    def get_total_remaining(self) -> float:
        return sum(by.amount for by in self.benefit_years.values())

    def get_remaining_days(self) -> int:
        return self.remaining_days

    def get_benefit_years(self) -> list[BenefitYear]:
        return list(self.benefit_years.values())
