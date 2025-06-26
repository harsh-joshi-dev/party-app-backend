from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    phone: str
    password: str
    user_type: str  # admin or employee
    username: Optional[str] = None
    company_id: Optional[str] = None
    company_name: Optional[str] = None
    address: Optional[str] = None
    alt_phone: Optional[str] = None
    email: Optional[str] = None

class UserLogin(BaseModel):
    phone: str
    password: str

class PasswordReset(BaseModel):
    phone: str
    new_password: str
