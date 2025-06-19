from fastapi import APIRouter, HTTPException
from models.payment import PaymentCreate
from config.database import payments_collection
from bson import ObjectId

router = APIRouter()

@router.post("/")
async def pay_employee(data: PaymentCreate):
    payments_collection.insert_one(data.dict())
    return {"message": "Payment added"}

@router.get("/")
async def get_payments(company_id: str):
    return list(payments_collection.find({"company_id": company_id}))

@router.put("/{id}")
async def update_payment(id: str, data: PaymentCreate):
    result = payments_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": data.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {"message": "Payment updated"}