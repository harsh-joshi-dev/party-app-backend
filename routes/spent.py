from fastapi import APIRouter, HTTPException
from models.spent import SpentCreate
from config.database import spents_collection, payments_collection
from bson import ObjectId
from datetime import datetime

router = APIRouter()

@router.post("/")
async def add_spent(data: SpentCreate):
    spents_collection.insert_one(data.dict())
    return {"message": "Spent added"}

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
    for key in set(list(spent_summary.keys()) + list(payment_summary.keys())):
        combined[key] = spent_summary.get(key, 0) + payment_summary.get(key, 0)

    total_spent = sum(combined.values())
    return {"monthly_spent_summary": combined, "total_spent": total_spent}
