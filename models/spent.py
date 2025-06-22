from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class SpentCreate(BaseModel):
    company_id: str
    type: str  # "Salary" or "Expense"
    
    # Salary fields
    salary_person: Optional[str]
    salary_from: Optional[date]
    salary_to: Optional[date]
    salary_given_date: Optional[date]
    salary_given_by: Optional[str]
    salary_payment_type: Optional[str]  # Gpay or Cash

    # Expense fields
    item_name: Optional[str]
    expense_payment_type: Optional[str]  # Gpay or Cash
    expense_source: Optional[str]  # Online or Offline
    expense_source_url_or_site: Optional[str]

    # Common
    amount: float
    bought_date: date
    note: Optional[str]
