from fastapi import APIRouter
from config.database import appointments_collection, spents_collection

router = APIRouter()

@router.get("/financial-summary")
async def financial_summary(company_id: str):
    # 1. Appointments aggregation (booking + addons only)
    appointment_pipeline = [
        {"$match": {
            "company_id": company_id,
            "event_completed": {"$ne": "deleted"},
            "event_start_datetime": {"$exists": True},
        }},
        {"$addFields": {
            "booking_amount": {"$toDouble": "$booking_amount"},
            "cake_price": {"$toDouble": {"$ifNull": ["$cake_price", 0]}},
            "addon_total": {
                "$sum": {
                    "$map": {
                        "input": {"$ifNull": ["$tags", []]},
                        "as": "tag",
                        "in": {"$toDouble": {"$ifNull": ["$$tag.price", 0]}}
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

    # 2. Spent aggregation
    spent_pipeline = [
        {"$match": {"company_id": company_id}},
        {"$group": {
            "_id": {
                "year": {"$year": "$bought_date"},
                "month": {"$month": "$bought_date"}
            },
            "total_salary": {
                "$sum": {"$cond": [{"$eq": ["$type", "Salary"]}, "$amount", 0]}
            },
            "total_expense": {
                "$sum": {"$cond": [{"$eq": ["$type", "Expense"]}, "$amount", 0]}
            }
        }}
    ]
    spent_data = list(spents_collection.aggregate(spent_pipeline))

    # 3. Merge data
    summary = {}

    for item in appointment_data:
        m, y = item["_id"]["month"], item["_id"]["year"]
        key = f"{m:02d}-{y}"
        summary[key] = {
            "booking": item.get("total_booking_amount", 0),
            "addon": item.get("total_addon_amount", 0),
            "cake": item.get("total_cake_spent", 0),
            "salary": 0,
            "expense": 0
        }

    for item in spent_data:
        m, y = item["_id"]["month"], item["_id"]["year"]
        key = f"{m:02d}-{y}"
        if key not in summary:
            summary[key] = {"booking": 0, "addon": 0, "cake": 0, "salary": 0, "expense": 0}
        summary[key]["salary"] += item.get("total_salary", 0)
        summary[key]["expense"] += item.get("total_expense", 0)

    # 4. Build final summary
    final = []
    tb = ta = tc = ts = te = 0

    def sort_key(k): m, y = map(int, k.split("-")); return y, m

    for month in sorted(summary.keys(), key=sort_key):
        d = summary[month]
        income = d["booking"] + d["addon"]
        spent = d["salary"] + d["expense"]
        profit = income - spent

        tb += d["booking"]
        ta += d["addon"]
        tc += d["cake"]
        ts += d["salary"]
        te += d["expense"]

        final.append({
            "month": month,
            "booking_amount": round(d["booking"], 2),
            "addon_amount": round(d["addon"], 2),
            "total_income": round(income, 2),
            "salary_spent": round(d["salary"], 2),
            "expense_spent": round(d["expense"], 2),
            "cake_cost": round(d["cake"], 2),
            "total_spent": round(spent, 2),
            "gross_earning": round(profit, 2)
        })

    return {
        "monthly_summary": final,
        "total_booking_amount": round(tb, 2),
        "total_addon_amount": round(ta, 2),
        "total_income": round(tb + ta, 2),
        "total_salary_spent": round(ts, 2),
        "total_expense_spent": round(te, 2),
        "total_cake_cost": round(tc, 2),
        "total_spent": round(ts + te, 2),
        "total_gross_earning": round((tb + ta) - (ts + te), 2)
    }
