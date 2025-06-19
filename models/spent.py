from pydantic import BaseModel
from typing import Optional
from datetime import date

class SpentCreate(BaseModel):
    buyer_name: str
    item_name: str
    amount: float
    bought_date: date
    note: Optional[str]
    company_id: str