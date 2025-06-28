from pydantic import BaseModel
from typing import Optional
from datetime import date

class SpentCreate(BaseModel):
    company_id: str
    type: str
    amount: float
    note: Optional[str] = None
    bought_date: Optional[date] = None

    # Salary-specific fields
    salary_person: Optional[str]
    salary_month: Optional[str]  # example: "June 2025"
    salary_given_date: Optional[date]
    salary_given_by: Optional[str]
    salary_payment_type: Optional[str]

    # Expense-specific fields
    item_name: Optional[str]
    expense_payment_type: Optional[str]
    expense_source: Optional[str]
    expense_source_url_or_site: Optional[str]
