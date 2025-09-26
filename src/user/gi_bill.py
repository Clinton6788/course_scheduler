from config.settings import (
    GRANT_OPP,
    GRANT_PELL,
    GI_BILL,
    GI_BILL_START,
    GI_BILL_END,
    BENEFITS_ASOF,
    BENEFITS_TIME,
    SESSIONS
)
from dataclasses import dataclass
import datetime as dt
from src.scheduling.sessions import Session

@dataclass
class BenefitYear:
    st: dt.date
    end: dt.date
    amount: float


class FinanceMGR:
    """Singleton Financial Manager for benefits"""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, hist_sessions):
        if not hasattr(self, '_initialized'):
            self.gis = {} # GI Bill storage
            self.gi_days = 0
            self._get_init_config(hist_sessions)

            self._initialized = True

    def _get_init_config(self, hist_sessions):
        """
        Initializes GI Bill days based on known remaining time and historical sessions.
        Charges full duration for any sessions in the past or currently running.
        
        Args:
            hist_sessions (list[Session]): List of sessions that are completed or in progress
        """
        # Convert remaining benefit time to days
        m, d = BENEFITS_TIME
        self.gi_days = m * 30 + d

        # Subtract full session days for fixed sessions
        self._charge_days(hist_sessions, final=True)
        self._charge_benefits(hist_sessions, final=True)

    def charge(self, charge_type: str, check_type: str, sess_data: Session | dict, final: bool = False) -> int:
        """
        Charge or check cost/days for one or more sessions.

        Args:
            charge_type (str): Type of charge to process. Must be either 'cost' or 'days'.
            check_type (str): 'sess' to charge a single session, 'full' to charge all sessions.
            sess_data (Session | dict): A single Session or dict of session_num -> Session.
            final (bool): If True, commits the charge. If False, performs a tentative check.

        Raises:
            AssertionError: On invalid inputs.

        Returns:
            int: Amount remaining after the charge; can be negative.
        """
        # Validate session inputs and flatten to list
        sess_list = self._validate_flatten(charge_type, check_type, sess_data)

        # Route based on charge type
        if charge_type == 'cost':
            return self._charge_benefits(sess_list, final=final)
        elif charge_type == 'days':
            return self._charge_days(sess_list, final=final)
        else:
            raise AssertionError(f"Invalid charge_type: {charge_type}")

    def _charge_days(self, sess_list: list, final: bool = False) -> int: # Done
        """
        Charge GI Bill days for a list of sessions.

        Args:
            sess_list (list[Session]): List of sessions to charge for
            final (bool): If True, commit the changes to self.gi_days; else return result only

        Returns:
            int: Remaining GI Bill days after charge (actual or simulated)
        """
        sess_list.sort(key=lambda s: s.start_date)

        days_used = 0
        for ses in sess_list:
            assert isinstance(ses, Session), f"Not a Session || {type(ses)}"

            # Only charge sessions that are current or in the future of BENEFITS_ASOF
            if ses.end_date >= BENEFITS_ASOF:
                # FULL SESSION CHARGE regardless of today
                days_used += 56  # Full 8 weeks

        remaining = self.gi_days - days_used

        if final:
            self.gi_days = remaining

        return remaining

    def _charge_benefits(self, sess_list: list, final: bool = False) -> float: # Done
        """
        Charge sessions against available GI Bill benefit years.
        
        Each session's cost is charged to the appropriate BenefitYear, 
        determined by the session's start date. If the year doesn't exist,
        it will be created. If `final` is False, no changes are committed.

        Args:
            sess_list (list[Session]): Sessions to charge
            final (bool): Whether to apply the charges

        Returns:
            float: Remaining benefits (positive or negative)
        """
        sess_list.sort(key=lambda s: s.start_date)

        gis_copy = {k: BenefitYear(v.st, v.end, v.amount) for k, v in self.gis.items()}
        total_remaining = 0.0

        for ses in sess_list:
            assert isinstance(ses, Session), f"Not a Session || {type(ses)}"

            ses_date = ses.start_date
            ses_cost = ses.tot_cost 

            year_start = dt.date(ses_date.year, *GI_BILL_START)
            # If start date is before cutoff, still in the previous benefit year
            if ses_date < year_start:
                year_start = dt.date(ses_date.year - 1, *GI_BILL_START)

            year_end = dt.date(year_start.year + 1, *GI_BILL_END)

            # Get or create the benefit year
            if year_start not in gis_copy:
                gis_copy[year_start] = BenefitYear(st=year_start, end=year_end, amount=GI_BILL)

            # Charge session cost
            # Adjust for grants
            ses_cost = min((ses_cost - GRANT_OPP - GRANT_PELL),0)
            gis_copy[year_start].amount -= ses_cost

        # If final, commit the charges
        if final:
            self.gis = gis_copy

        # Return the total remaining across all benefit years
        total_remaining = sum(by.amount for by in gis_copy.values())
        return total_remaining
            
    def _validate_flatten(self, check_type: str, charge_type: str, sess_data: Session | dict) -> list: # Done
        """
        Internal utility to validate input arguments and flatten session data into a list.

        Args:
            check_type (str): Either 'sess' (single session) or 'full' (all sessions).
            charge_type (str): The charge category to check. Must be either 'cost' or 'days'.
            sess_data (Session | dict): A single Session object or a dictionary of session_num -> Session.

        Returns:
            list: A list of Session objects to be processed.

        Raises:
            AssertionError: If any argument is invalid or improperly structured.
        """
        assert charge_type in ['cost', 'days']
        assert check_type in ['sess', 'full'], f"Incorrect charge type||{check_type}"

        sess_list = []
        if check_type == 'sess':
            assert isinstance(sess_data, Session), f"Sess_data MUST be Session||{type(sess_data)}"
            sess_list.append(sess_data)
        else:
            assert isinstance(sess_data, dict), f"Sess Data MUST be DICT||{type(sess_data)}"
            for s in sess_data.values():
                assert isinstance(s, Session), f"Sessions MUST be Session instance||{type(s)}"
                sess_list.append(s)
        return sess_list