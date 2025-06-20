from pydantic import BaseModel
from typing import List, Optional
from datetime import date, time

# Define a Tag model for each tag item
class Tag(BaseModel):
    name: str
    price: str

# Main schema for appointment creation
class AppointmentCreate(BaseModel):
    customer_name: str
    customer_phone: str
    event_date: date
    event_start_time: time
    event_end_time: time
    hours: str
    tags: List[Tag]  # Now supports list of objects with name and price
    booking_amount: str
    need_cake: bool
    cake_weight: Optional[str] = None
    note: Optional[str] = None
    company_id: str
    payment_status: str
    payment_type: Optional[str] = None
    event_type: str
    event_completed: str
    cake_price: Optional[float] = None
    cake_note: Optional[str] = None