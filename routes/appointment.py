from fastapi import APIRouter, HTTPException
from models.appointment import AppointmentCreate
from config.database import appointments_collection
from bson import ObjectId
from datetime import datetime, date, time

router = APIRouter()

def is_overlap(start1, end1, start2, end2):
    return start1 < end2 and start2 < end1  # True if the time ranges overlap

# Create Appointment with overlap validation
@router.post("/")
async def create_appointment(data: AppointmentCreate):
    appointment_dict = data.dict()

    if not (appointment_dict.get("event_date") and appointment_dict.get("event_start_time") and appointment_dict.get("event_end_time")):
        raise HTTPException(status_code=400, detail="Missing date or time fields")

    event_start = datetime.combine(appointment_dict["event_date"], appointment_dict["event_start_time"])
    event_end = datetime.combine(appointment_dict["event_date"], appointment_dict["event_end_time"])
    appointment_dict["event_start_datetime"] = event_start
    appointment_dict["event_end_datetime"] = event_end

    # Overlap check
    overlapping = appointments_collection.find_one({
        "company_id": appointment_dict["company_id"],
        "event_completed": {"$ne": "deleted"},
        "event_start_datetime": {"$lt": event_end},
        "event_end_datetime": {"$gt": event_start}
    })

    if overlapping:
        raise HTTPException(status_code=409, detail="Slot is already booked for the selected time.")

    result = appointments_collection.insert_one(appointment_dict)
    return {"message": "Appointment created", "id": str(result.inserted_id)}

# Mark Event as Completed
@router.put("/complete/{id}")
async def mark_event_completed(id: str):
    result = appointments_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"event_completed": "true"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"message": "Event marked as completed"}


@router.get("/")
async def get_appointments(company_id: str):
    now = datetime.now()
    appointments = list(appointments_collection.find({
        "company_id": company_id,
        "event_completed": {"$ne": "deleted"}
    }))

    for appt in appointments:
        if appt.get("event_end_datetime") and isinstance(appt["event_end_datetime"], datetime):
            if appt["event_end_datetime"] < now and appt.get("event_completed") != "true":
                appointments_collection.update_one(
                    {"_id": appt["_id"]},
                    {"$set": {"event_completed": "true"}}
                )
                appt["event_completed"] = "true"

    for item in appointments:
        item["_id"] = str(item["_id"])
        if "event_date" in item and isinstance(item["event_date"], date):
            item["event_date"] = item["event_date"].isoformat()
        if "event_start_time" in item and isinstance(item["event_start_time"], time):
            item["event_start_time"] = item["event_start_time"].isoformat()
        if "event_end_time" in item and isinstance(item["event_end_time"], time):
            item["event_end_time"] = item["event_end_time"].isoformat()

    return {
        "active": [a for a in appointments if a.get("event_completed") != "true"],
        "completed": [a for a in appointments if a.get("event_completed") == "true"]
    }


# Delete Appointment
@router.delete("/{id}")
async def delete_appointment(id: str, reason: str, deleted_by: str, refund_amount: float = 0.0, refund_reason: str = ""):
    delete_info = {
        "event_completed": "deleted",
        "deleted_at": datetime.now(),
        "delete_reason": reason,
        "refund_amount": refund_amount,
        "refund_reason": refund_reason,
        "deleted_by": deleted_by
    }
    result = appointments_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": delete_info}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"message": "Appointment marked as deleted with reason"}


@router.get("/deleted")
async def get_deleted_appointments(company_id: str):
    deleted = list(appointments_collection.find({
        "company_id": company_id,
        "event_completed": "deleted"
    }))
    for item in deleted:
        item["_id"] = str(item["_id"])
    return deleted


# Update Appointment
@router.put("/{id}")
async def update_appointment(id: str, data: AppointmentCreate, edited_by: str = "Unknown"):
    update_data = data.dict()

    if update_data.get("event_date") and update_data.get("event_start_time"):
        update_data["event_start_datetime"] = datetime.combine(update_data["event_date"], update_data["event_start_time"])
    if update_data.get("event_date") and update_data.get("event_end_time"):
        update_data["event_end_datetime"] = datetime.combine(update_data["event_date"], update_data["event_end_time"])

    update_data["last_edited_by"] = edited_by
    update_data["last_edited_at"] = datetime.now()

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
