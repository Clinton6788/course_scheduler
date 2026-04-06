import datetime as dt
from dataclasses import dataclass
from dateutil.relativedelta import relativedelta
from typing import Optional

from src.scheduling import Session


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
        start_date = dt.date(dt.date.today().year, *start_dt)
        end_date = start_date + relativedelta(years=1) - dt.timedelta(days=1)

        self.yearly_amount = yearly_amount
        self.benefit_start = start_date
        self.active_benefit_year = BenefitYear(start_date, end_date, yearly_amount)

        self.benefit_years: dict[dt.date, BenefitYear] = {
            start_date: self.active_benefit_year
        }

        m, d = remaining_time
        self.remaining_days = m * 30 + d  # still approximate by design
        self.asof = days_as_of

        # Track charged session IDs
        self.charged_sessions: list[int] = []

    # =====================
    # Historical charging
    # =====================
    def charge_historical(self, sessions: list[Session]) -> None:
        for s in sorted(sessions, key=lambda x: x.start_date):
            if s.num in self.charged_sessions:
                continue

            # Sessions before asof are already accounted for in remaining_days.
            # They still get dollar coverage but should NOT deduct days.
            if s.start_date < self.asof:
                was_covered = True if self.remaining_days > 0 else False
            else:
                was_covered = self._charge_days(s, final=True)
            user_owes, coverage = self._charge_cost(s, was_covered, final=True)

            self.charged_sessions.append(s.num)
            s.add_gib(coverage)
            s.gib_remaining = self.active_benefit_year.amount

        # Ensure active year is the present one
        self._get_or_create_benefit_year(dt.date.today())

    # =====================
    # Live / simulated charge
    # =====================
    def charge_session(self, sess: Session, final: bool = False) -> tuple[bool, float]:
        assert isinstance(sess, Session), f"Invalid session: {type(sess)}"

        if sess.num in self.charged_sessions:
            print(f"Already charged session {sess.num}")
            return False, 0.0

        ses_covered = self._charge_days(sess, final)
        charge_amount, coverage = self._charge_cost(sess, ses_covered, final)

        if final:
            self.charged_sessions.append(sess.num)
            sess.add_gib(coverage)
            sess.gib_remaining = self.active_benefit_year.amount

        return ses_covered, charge_amount

    # =====================
    # Internal helpers
    # =====================
    def _charge_days(
        self,
        session: Session,
        final: bool,
        ignore_asof: bool = False,
    ) -> bool:
        """
        Determines if GI Bill can cover the given session.
        """
        if self.remaining_days <= 0:
            return False

        if not ignore_asof and session.start_date < self.asof:
            return False

        # inclusive session length
        session_duration = (session.end_date - session.start_date).days + 1
        updated_remaining = self.remaining_days - session_duration

        if final:
            self.remaining_days = max(0, updated_remaining)

        return True

    def _charge_cost(
        self,
        session: Session,
        was_covered: bool,
        final: bool,
    ) -> tuple[float, float]:
        """
        Deducts the session cost from the appropriate benefit year.

        Always returns:
            (user_owes, coverage)
        """
        ses_cost = session.adj_cost

        # If not covered by GI Bill at all
        if not was_covered:
            return ses_cost, 0.0

        # -------------------------
        # Resolve benefit year
        # -------------------------
        if final:
            year = self._get_or_create_benefit_year(session.start_date)
        else:
            # Work on a copy for simulation
            real_year = self._get_or_create_benefit_year(session.start_date)
            year = BenefitYear(real_year.st, real_year.end, real_year.amount)

        # -------------------------
        # Apply coverage
        # -------------------------
        coverage = min(ses_cost, year.amount)
        user_owes = ses_cost - coverage

        if final:
            year.amount -= coverage
        # else: simulated copy, discard changes

        return user_owes, coverage

    # =====================
    # Introspection helpers
    # =====================
    def get_total_remaining(self, year: dt.date) -> float:
        by = self.benefit_years.get(year)
        return by.amount if by else 0.0

    def get_remaining_days(self) -> int:
        return self.remaining_days

    def _get_or_create_benefit_year(self, ref_date: dt.date) -> BenefitYear:
        """
        Returns the benefit year covering ref_date.
        Creates missing years and updates active_benefit_year.
        """
        year_start = dt.date(
            ref_date.year,
            self.benefit_start.month,
            self.benefit_start.day,
        )
        if ref_date < year_start:
            year_start = year_start.replace(year=year_start.year - 1)

        if year_start not in self.benefit_years:
            year_end = year_start + relativedelta(years=1) - dt.timedelta(days=1)
            self.benefit_years[year_start] = BenefitYear(
                year_start, year_end, self.yearly_amount
            )

        self.active_benefit_year = self.benefit_years[year_start]
        return self.active_benefit_year
