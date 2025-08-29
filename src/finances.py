from settings import (
    GRANT_OPP,
    GRANT_PELL,
    GI_BILL,
    GI_BILL_START,
    GI_BILL_END,
    BENEFITS_ASOF,
    BENEFITS_TIME
)
from dataclasses import dataclass
from datetime import date


@dataclass
class BenefitYear:
    st: date
    end: date
    amount: float = GI_BILL


class GIBill:
    def __init__(self):
        self.benefit_years = {}
        self.days = 

    def charge_session(self, session):
        """Charge 'amount' to GI bill. 
        
        Returns:
            int: Amount NOT covered. '0' if fully covered
        """
        
        if self.amount <= 0:
            return amount
    
        if self.amount >= amount:
            self.amount -= amount
            return 0
        
        a = amount - self.amount
        self.amount = 0
        return a
        

class FinanceMgr:
    def __init__(self):
        self.gi = None
        self.sessions = {}

    def charge_sessions(self, sessions):

