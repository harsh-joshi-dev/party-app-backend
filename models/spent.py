from pydantic import BaseModel
from typing import Optional
from datetime import date

class SpentCreate(BaseModel):
    company_id: Optional[str] = None
    type: Optional[str] = None
    amount: Optional[float] = None
    note: Optional[str] = None
    bought_date: Optional[date] = None

    # Salary-specific fields
    salary_person: Optional[str] = None
    salary_month: Optional[str] = None  # example: "June 2025"
    salary_given_date: Optional[date] = None
    salary_given_by: Optional[str] = None
    salary_payment_type: Optional[str] = None

    # Expense-specific fields
    item_name: Optional[str] = None
    expense_payment_type: Optional[str] = None
    expense_source: Optional[str] = None
    expense_source_url_or_site: Optional[str] = None
