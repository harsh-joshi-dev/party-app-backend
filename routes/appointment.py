from fastapi import APIRouter, HTTPException
from models.appointment import AppointmentCreate
from config.database import appointments_collection
from bson import ObjectId
from datetime import datetime, date, time

router = APIRouter()

# Create Appointment
@router.post("/")
async def create_appointment(data: AppointmentCreate):
    appointment_dict = data.dict()

    # Combine event_date and event_start_time/end_time into datetime objects
    if isinstance(appointment_dict["event_date"], date) and isinstance(appointment_dict["event_start_time"], time):
        appointment_dict["event_start_datetime"] = datetime.combine(appointment_dict["event_date"], appointment_dict["event_start_time"])
    if isinstance(appointment_dict["event_date"], date) and isinstance(appointment_dict["event_end_time"], time):
        appointment_dict["event_end_datetime"] = datetime.combine(appointment_dict["event_date"], appointment_dict["event_end_time"])

    # Remove raw date/time fields if not needed
    appointment_dict.pop("event_date", None)
    appointment_dict.pop("event_start_time", None)
    appointment_dict.pop("event_end_time", None)

    result = appointments_collection.insert_one(appointment_dict)
    return {"message": "Appointment created", "id": str(result.inserted_id)}

# Get All Appointments
@router.get("/")
async def get_appointments(company_id: str):
    appointments = list(appointments_collection.find({"company_id": company_id}))
    for item in appointments:
        item["_id"] = str(item["_id"])
    return appointments

# Delete Appointment
@router.delete("/{id}")
async def delete_appointment(id: str):
    result = appointments_collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"message": "Deleted"}

# Update Appointment
@router.put("/{id}")
async def update_appointment(id: str, data: AppointmentCreate):
    update_data = data.dict()

    if isinstance(update_data["event_date"], date) and isinstance(update_data["event_start_time"], time):
        update_data["event_start_datetime"] = datetime.combine(update_data["event_date"], update_data["event_start_time"])
    if isinstance(update_data["event_date"], date) and isinstance(update_data["event_end_time"], time):
        update_data["event_end_datetime"] = datetime.combine(update_data["event_date"], update_data["event_end_time"])

    update_data.pop("event_date", None)
    update_data.pop("event_start_time", None)
    update_data.pop("event_end_time", None)

    result = appointments_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"message": "Appointment updated"}

# Monthly Summary (Grouped by event_datetime)
@router.get("/monthly-summary")
async def monthly_summary(company_id: str):
    pipeline = [
        {"$match": {"company_id": company_id}},
        {"$group": {
            "_id": {
                "month": {"$month": "$event_start_datetime"},
                "year": {"$year": "$event_start_datetime"},
            },
            "total_appointments": {"$sum": 1},
            "total_amount": {"$sum": {"$toDouble": "$booking_amount"}},
        }},
        {"$sort": {"_id.year": 1, "_id.month": 1}}
    ]
    result = list(appointments_collection.aggregate(pipeline))
    total_appointments = appointments_collection.count_documents({"company_id": company_id})

    total_amount = sum(doc["total_amount"] for doc in result)

    return {
        "monthly_summary": result,
        "total_appointments": total_appointments,
        "total_amount": total_amount
    }
