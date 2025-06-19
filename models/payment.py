from pydantic import BaseModel
from datetime import date

class PaymentCreate(BaseModel):
    employee_name: str
    amount: float
    paid_date: date
    company_id: str