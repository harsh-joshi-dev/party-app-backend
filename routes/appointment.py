from fastapi import APIRouter, HTTPException
from models.appointment import AppointmentCreate
from config.database import appointments_collection
from bson import ObjectId
from datetime import datetime

router = APIRouter()

@router.post("/")
async def create_appointment(data: AppointmentCreate):
    result = appointments_collection.insert_one(data.dict())
    return {"message": "Appointment created", "id": str(result.inserted_id)}

@router.get("/")
async def get_appointments(company_id: str):
    return list(appointments_collection.find({"company_id": company_id}))

@router.delete("/{id}")
async def delete_appointment(id: str):
    result = appointments_collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"message": "Deleted"}

@router.put("/{id}")
async def update_appointment(id: str, data: AppointmentCreate):
    result = appointments_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": data.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"message": "Appointment updated"}

@router.get("/monthly-summary")
async def monthly_summary(company_id: str):
    pipeline = [
        {"$match": {"company_id": company_id}},
        {"$group": {
            "_id": {"month": {"$month": "$event_date"}, "year": {"$year": "$event_date"}},
            "total_appointments": {"$sum": 1},
            "total_amount": {"$sum": "$booking_amount"},
        }},
        {"$sort": {"_id.year": 1, "_id.month": 1}}
    ]
    result = list(appointments_collection.aggregate(pipeline))
    total_appointments = appointments_collection.count_documents({"company_id": company_id})
    total_amount = sum(doc["total_amount"] for doc in result)
    return {"monthly_summary": result, "total_appointments": total_appointments, "total_amount": total_amount}
