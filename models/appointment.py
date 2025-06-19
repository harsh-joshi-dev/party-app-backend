
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, time

class AppointmentCreate(BaseModel):
    customer_name: str
    customer_phone: str
    event_date: date
    event_time: time
    hours: int
    tags: Optional[List[str]] = []
    booking_amount: float
    need_cake: bool
    cake_weight: Optional[float] = None
    note: Optional[str] = None
    company_id: str
    payment: bool
    payment_type: str
