from fastapi import APIRouter
from config.database import appointments_collection, spents_collection

router = APIRouter()

@router.get("/financial-summary")
async def financial_summary(company_id: str):
    # 1. Aggregate from appointments: booking + addon (tags) + cake
    appointment_pipeline = [
        {"$match": {
            "company_id": company_id,
            "event_completed": {"$ne": "deleted"},
            "event_start_datetime": {"$exists": True},
        }},
        {"$addFields": {
            "booking_amount": {"$toDouble": {"$ifNull": ["$booking_amount", "0"]}},
            "cake_price": {"$toDouble": {"$ifNull": ["$cake_price", 0]}},
            "addon_total": {
                "$sum": {
                    "$map": {
                        "input": {"$ifNull": ["$tags", []]},
                        "as": "tag",
                        "in": {"$toDouble": {"$ifNull": ["$$tag.price", "0"]}}
                    }
                }
            }
        }},
        {"$group": {
            "_id": {
                "year": {"$year": "$event_start_datetime"},
                "month": {"$month": "$event_start_datetime"}
            },
            "total_booking_amount": {"$sum": "$booking_amount"},
            "total_addon_amount": {"$sum": "$addon_total"},
            "total_cake_spent": {"$sum": "$cake_price"}
        }}
    ]
    appointment_data = list(appointments_collection.aggregate(appointment_pipeline))

    # 2. Aggregate Spents: Salary and Expense
    spent_pipeline = [
        {"$match": {"company_id": company_id}},
        {"$group": {
            "_id": {
                "year": {"$year": "$bought_date"},
                "month": {"$month": "$bought_date"}
            },
            "total_salary": {
                "$sum": {
                    "$cond": [{"$eq": ["$type", "Salary"]}, "$amount", 0]
                }
            },
            "total_expense": {
                "$sum": {
                    "$cond": [{"$eq": ["$type", "Expense"]}, "$amount", 0]
                }
            }
        }}
    ]
    spent_data = list(spents_collection.aggregate(spent_pipeline))

    # 3. Combine data into summary dict
    summary = {}

    for item in appointment_data:
        m, y = item["_id"].get("month"), item["_id"].get("year")
        if m is None or y is None: continue
        key = f"{m:02d}-{y}"
        summary[key] = {
            "booking": item.get("total_booking_amount", 0),
            "addon": item.get("total_addon_amount", 0),
            "cake": item.get("total_cake_spent", 0),
            "salary": 0,
            "expense": 0
        }

    for item in spent_data:
        m, y = item["_id"].get("month"), item["_id"].get("year")
        if m is None or y is None: continue
        key = f"{m:02d}-{y}"
        if key not in summary:
            summary[key] = {"booking": 0, "addon": 0, "cake": 0, "salary": 0, "expense": 0}
        summary[key]["salary"] += item.get("total_salary", 0)
        summary[key]["expense"] += item.get("total_expense", 0)

    # 4. Final response format
    final = []
    tb = ta = tc = ts = te = 0

    def sort_key(k): 
        m, y = map(int, k.split("-"))
        return y, m

    for month in sorted(summary.keys(), key=sort_key):
        d = summary[month]
        total_income = d["booking"] + d["addon"]
        amount_spent = d["salary"] + d["expense"]
        left = total_income - amount_spent

        tb += d["booking"]
        ta += d["addon"]
        tc += d["cake"]
        ts += d["salary"]
        te += d["expense"]

        final.append({
            "month": month,
            "total_booking_amount": round(d["booking"], 2),
            "total_addon_amount": round(d["addon"], 2),
            "total_income": round(total_income, 2),
            "amount_spent_on_salary": round(d["salary"], 2),
            "total_expense": round(d["expense"], 2),
            "amount_spent": round(amount_spent, 2),
            "total_spent_on_cake": round(d["cake"], 2),
            "amount_left": round(left, 2)
        })

    return {
        "monthly_summary": final,
        "total_booking_amount": round(tb, 2),
        "total_addon_amount": round(ta, 2),
        "total_income": round(tb + ta, 2),
        "total_spent_on_salary": round(ts, 2),
        "total_expense": round(te, 2),
        "total_spent": round(ts + te, 2),
        "total_spent_on_cake": round(tc, 2),
        "total_left": round((tb + ta) - (ts + te), 2)
    }
