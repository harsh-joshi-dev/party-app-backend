from fastapi import APIRouter, HTTPException
from models.user import UserCreate, UserLogin, PasswordReset, UserCreateCompany
from config.database import db
from utils import hash_password, verify_password

router = APIRouter()

@router.post("/create-company")
async def create_company(data: UserCreateCompany):
    if data.user_type.lower() != "admin":
        raise HTTPException(status_code=400, detail="user_type must be 'admin' for company creation")

    existing = db["users"].find_one({"phone": data.phone})
    if existing:
        raise HTTPException(status_code=400, detail="Phone already registered")

    company = {
        "company_name": data.company_name,
        "address": data.address,
        "phone": data.phone,
        "password": hash_password(data.password),
        "user_type": "admin",
        "alt_phone": data.alt_phone,
        "email": data.email,
    }

    result = db["users"].insert_one(company)
    return {
        "message": "Company created successfully",
        "company_id": str(result.inserted_id),
        "company_name": data.company_name,
        "user_type": "admin"
    }


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

    if not user or not verify_password(data.password, user.get("password", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_type = user.get("user_type")
    if not user_type:
        raise HTTPException(status_code=400, detail="User type not found in user data")

    is_company = user_type == "admin"
    company_id = str(user["_id"]) if is_company else str(user.get("company_id"))

    if not company_id:
        raise HTTPException(status_code=400, detail="Company ID missing")

    return {
        "message": "Login successful",
        "company_id": company_id,
        "user_type": user_type,
        "username": user.get("username", "")
    }

@router.post("/create-employee")
async def create_employee(data: UserCreate):
    if not data.company_id:
        raise HTTPException(status_code=400, detail="company_id is required for employee")

    existing = db["users"].find_one({"phone": data.phone})
    if existing:
        raise HTTPException(status_code=400, detail="Phone already registered")

    employee = {
        "username": data.username,
        "phone": data.phone,
        "password": hash_password(data.password),
        "user_type": "employee",
        "company_id": data.company_id,
        "alt_phone": data.alt_phone,
        "email": data.email,
    }

    db["users"].insert_one(employee)
    return {"message": "Employee created successfully"}

@router.get("/employees/{company_id}")
async def get_employees_by_company(company_id: str):
    employees = db["users"].find({"company_id": company_id, "user_type": "employee"})
    result = []
    for emp in employees:
        result.append({
            "_id": str(emp["_id"]),
            "username": emp.get("username"),
            "phone": emp.get("phone"),
            "email": emp.get("email"),
        })
    return {"employees": result}


@router.get("/appointments/{company_id}")
async def get_appointments_by_company(company_id: str):
    appointments = db["appointments"].find({"company_id": company_id})
    return {"appointments": [dict(appt, _id=str(appt["_id"])) for appt in appointments]}


@router.post("/reset-password")
async def reset_password(data: PasswordReset):
    user = db["users"].find_one({"phone": data.phone})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db["users"].update_one({"phone": data.phone}, {"$set": {"password": hash_password(data.new_password)}})
    return {"message": "Password reset successfully"}
