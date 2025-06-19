from pydantic import BaseModel
from typing import Optional, List
from datetime import date, time

class AppointmentCreate(BaseModel):
    customer_name: str
    customer_phone: str
    event_date: date
    event_start_time: time
    event_end_time: time
    hours: str
    tags: Optional[List[str]] = []
    booking_amount: str
    need_cake: bool
    cake_weight: Optional[str] = None
    note: Optional[str] = None
    company_id: str
    payment_status: str
    payment_type: str
    event_type: str
