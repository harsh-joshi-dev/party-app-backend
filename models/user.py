from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    company_name: str
    address: str
    username: str
    password: str
    phone: str
    alt_phone: Optional[str]

class UserLogin(BaseModel):
    phone: str
    password: str

class PasswordReset(BaseModel):
    phone: str
    new_password: str
