from fastapi import APIRouter, HTTPException
from models.spent import SpentCreate
from config.database import spents_collection, payments_collection, deleted_spents_collection
from bson import ObjectId
from datetime import datetime, date

router = APIRouter()

def convert_date_fields(d: dict):
    for key, value in d.items():
        if isinstance(value, date) and not isinstance(value, datetime):
            d[key] = datetime.combine(value, datetime.min.time())
    return d

@router.post("/")
async def add_spent(data: SpentCreate):
    if data.type == "Salary":
        if not all([data.salary_person, data.salary_month, data.salary_given_by, data.salary_payment_type]):
            raise HTTPException(status_code=400, detail="Missing salary-related fields")

        existing = spents_collection.find_one({
            "type": "Salary",
            "salary_person": data.salary_person,
            "company_id": data.company_id,
            "salary_month": data.salary_month
        })
        if existing:
            raise HTTPException(status_code=409, detail="Salary already given for this month")

    elif data.type == "Expense":
        if not all([data.item_name, data.expense_payment_type, data.expense_source]):
            raise HTTPException(status_code=400, detail="Missing expense-related fields")
        if data.expense_source == "Online" and not data.expense_source_url_or_site:
            raise HTTPException(status_code=400, detail="Provide site name or URL for online purchases")

    spent_dict = data.dict()
    spent_dict = convert_date_fields(spent_dict)
    spent_dict["created_at"] = datetime.now()

    spents_collection.insert_one(spent_dict)
    return {"message": "Spent record added successfully"}

@router.get("/")
async def get_spents(company_id: str):
    return list(spents_collection.find({"company_id": company_id}))


@router.put("/{id}")
async def update_spent(id: str, data: SpentCreate):
    result = spents_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": data.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Spent record not found")
    return {"message": "Spent record updated"}


@router.delete("/{id}")
async def delete_spent(id: str, reason: str):
    if not reason:
        raise HTTPException(status_code=400, detail="Reason for deletion is required")
    
    record = spents_collection.find_one({"_id": ObjectId(id)})
    if not record:
        raise HTTPException(status_code=404, detail="Spent record not found")
    
    # Append metadata and store in deleted collection
    record["deleted_at"] = datetime.now()
    record["deleted_reason"] = reason
    deleted_spents_collection.insert_one(record)

    # Remove from main collection
    spents_collection.delete_one({"_id": ObjectId(id)})

    return {"message": "Spent record deleted and archived"}


@router.get("/deleted/list")
async def get_deleted_spents(company_id: str):
    return list(deleted_spents_collection.find({"company_id": company_id}))


@router.get("/monthly-summary")
async def spent_summary(company_id: str):
    spent_pipeline = [
        {"$match": {"company_id": company_id}},
        {"$group": {
            "_id": {"month": {"$month": "$bought_date"}, "year": {"$year": "$bought_date"}},
            "total_spent": {"$sum": "$amount"},
        }}
    ]
    payment_pipeline = [
        {"$match": {"company_id": company_id}},
        {"$group": {
            "_id": {"month": {"$month": "$paid_date"}, "year": {"$year": "$paid_date"}},
            "total_payment": {"$sum": "$amount"},
        }}
    ]

    spent_summary = {f"{d['_id']['month']}-{d['_id']['year']}": d["total_spent"] for d in spents_collection.aggregate(spent_pipeline)}
    payment_summary = {f"{d['_id']['month']}-{d['_id']['year']}": d["total_payment"] for d in payments_collection.aggregate(payment_pipeline)}

    combined = {}
    for key in set(spent_summary.keys()) | set(payment_summary.keys()):
        combined[key] = spent_summary.get(key, 0) + payment_summary.get(key, 0)

    total_spent = sum(combined.values())
    return {"monthly_spent_summary": combined, "total_spent": total_spent}
