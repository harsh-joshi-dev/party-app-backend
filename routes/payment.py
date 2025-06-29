from fastapi import APIRouter, HTTPException
from config.database import payments_collection, spents_collection, appointments_collection

router = APIRouter()

@router.get("/financial-summary")
async def financial_summary(company_id: str):
    # 1. Aggregate Payments
    payment_pipeline = [
        {"$match": {"company_id": company_id}},
        {"$group": {
            "_id": {
                "year": {"$year": "$paid_date"},
                "month": {"$month": "$paid_date"}
            },
            "total_payment": {"$sum": "$amount"}
        }}
    ]
    payment_data = list(payments_collection.aggregate(payment_pipeline))

    # 2. Aggregate Spents
    spent_pipeline = [
        {"$match": {"company_id": company_id}},
        {"$group": {
            "_id": {
                "year": {"$year": "$bought_date"},
                "month": {"$month": "$bought_date"}
            },
            "total_spent": {"$sum": "$amount"}
        }}
    ]
    spent_data = list(spents_collection.aggregate(spent_pipeline))

    # 3. Aggregate Cake Prices from Appointments
    cake_pipeline = [
        {"$match": {
            "company_id": company_id,
            "event_completed": {"$ne": "deleted"},
            "cake_price": {"$exists": True, "$gt": 0}
        }},
        {"$group": {
            "_id": {
                "year": {"$year": "$event_start_datetime"},
                "month": {"$month": "$event_start_datetime"}
            },
            "total_cake_spent": {"$sum": {"$toDouble": "$cake_price"}}
        }}
    ]
    cake_data = list(appointments_collection.aggregate(cake_pipeline))

    # 4. Merge All Data into a Unified Summary
    summary = {}

    # Payments
    for item in payment_data:
        month = item["_id"].get("month")
        year = item["_id"].get("year")
        if month is None or year is None:
            continue
        key = f"{month:02d}-{year}"
        summary[key] = {"payment": item["total_payment"], "spent": 0, "cake": 0}

    # Spents
    for item in spent_data:
        month = item["_id"].get("month")
        year = item["_id"].get("year")
        if month is None or year is None:
            continue
        key = f"{month:02d}-{year}"
        if key not in summary:
            summary[key] = {"payment": 0, "spent": 0, "cake": 0}
        summary[key]["spent"] += item["total_spent"]

    # Cake Costs
    for item in cake_data:
        month = item["_id"].get("month")
        year = item["_id"].get("year")
        if month is None or year is None:
            continue
        key = f"{month:02d}-{year}"
        if key not in summary:
            summary[key] = {"payment": 0, "spent": 0, "cake": 0}
        summary[key]["cake"] += item["total_cake_spent"]

    # 5. Compile Final Monthly Summary
    final_summary = []
    gross_payment = gross_spent = gross_cake = 0

    def sort_key(key: str):
        m, y = map(int, key.split("-"))
        return y, m

    for month_key in sorted(summary.keys(), key=sort_key):
        data = summary[month_key]
        payment = data.get("payment", 0)
        spent = data.get("spent", 0)
        cake = data.get("cake", 0)
        total_spent = spent + cake
        left = payment - total_spent

        gross_payment += payment
        gross_spent += spent
        gross_cake += cake

        final_summary.append({
            "month": month_key,
            "amount_paid": round(payment, 2),
            "amount_spent": round(spent, 2),
            "amount_spent_on_cake": round(cake, 2),
            "total_spent": round(total_spent, 2),
            "amount_left": round(left, 2)
        })

    # 6. Return Response
    return {
        "monthly_summary": final_summary,
        "total_paid": round(gross_payment, 2),
        "total_spent": round(gross_spent, 2),
        "total_cake_spent": round(gross_cake, 2),
        "gross_total_spent": round(gross_spent + gross_cake, 2),
        "total_left": round(gross_payment - (gross_spent + gross_cake), 2)
    }
