from fastapi import APIRouter, HTTPException
from models.user import UserCreate, UserLogin, PasswordReset
from config.database import db
from utils import hash_password, verify_password

router = APIRouter()

@router.post("/register")
async def register_user(data: UserCreate):
    existing = db["users"].find_one({"phone": data.phone})
    if existing:
        raise HTTPException(status_code=400, detail="Phone already registered")
    user = data.dict()
    user["password"] = hash_password(user["password"])
    db["users"].insert_one(user)
    return {"message": "User registered successfully"}

@router.post("/login")
async def login_user(data: UserLogin):
    user = db["users"].find_one({"phone": data.phone})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful", "company_id": str(user["_id"]) }

@router.post("/reset-password")
async def reset_password(data: PasswordReset):
    user = db["users"].find_one({"phone": data.phone})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db["users"].update_one({"phone": data.phone}, {"$set": {"password": hash_password(data.new_password)}})
    return {"message": "Password reset successfully"}