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
    user["user_type"] = "admin" if data.user_type == "company" else data.user_type
    db["users"].insert_one(user)
    return {"message": "User registered successfully", "user_type": user["user_type"]}


@router.get("/companies")
async def get_all_companies():
    users = db["users"].find({"user_type": "admin"})
    result = []
    for user in users:
        user_dict = {
            "_id": str(user.get("_id")),
            "company_name": user.get("company_name", ""),
            "address": user.get("address", ""),
            "username": user.get("username", ""),
            "phone": user.get("phone", ""),
            "alt_phone": user.get("alt_phone", ""),
        }
        result.append(user_dict)
    return {"companies": result}


@router.post("/login")
async def login_user(data: UserLogin):
    user = db["users"].find_one({"phone": data.phone})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {
        "message": "Login successful",
        "company_id": str(user.get("_id") if user.get("user_type") in ["admin", "company"] else user.get("company_id")),
        "user_type": user.get("user_type", "employee"),
        "username": user.get("username", "")
    }


@router.post("/create-employee")
async def create_employee(data: UserCreate):
    existing = db["users"].find_one({"phone": data.phone})
    if existing:
        raise HTTPException(status_code=400, detail="Phone already registered")

    if not data.company_id:
        raise HTTPException(status_code=400, detail="company_id required for employee")

    employee = data.dict()
    employee["password"] = hash_password(employee["password"])
    employee["user_type"] = "employee"
    employee["company_id"] = data.company_id

    db["users"].insert_one(employee)
    return {"message": "Employee added successfully"}


@router.get("/employees/{company_id}")
async def get_employees_by_company(company_id: str):
    employees = db["users"].find({"company_id": company_id, "user_type": "employee"})
    result = []
    for user in employees:
        result.append({
            "_id": str(user.get("_id")),
            "username": user.get("username"),
            "phone": user.get("phone"),
            "alt_phone": user.get("alt_phone", ""),
            "email": user.get("email", "")
        })
    return {"employees": result}


@router.get("/appointments/{company_id}")
async def get_appointments_by_company(company_id: str):
    appointments = db["appointments"].find({"company_id": company_id})
    result = []
    for appt in appointments:
        appt["_id"] = str(appt["_id"])
        result.append(appt)
    return {"appointments": result}


@router.post("/reset-password")
async def reset_password(data: PasswordReset):
    user = db["users"].find_one({"phone": data.phone})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db["users"].update_one({"phone": data.phone}, {"$set": {"password": hash_password(data.new_password)}})
    return {"message": "Password reset successfully"}
