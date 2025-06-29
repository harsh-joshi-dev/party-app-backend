from fastapi import APIRouter
from config.database import appointments_collection, spents_collection

router = APIRouter()

@router.get("/financial-summary")
async def financial_summary(company_id: str):
    # 1. Appointments: booking + add-ons + cake
    appointment_pipeline = [
        {"$match": {
            "company_id": company_id,
            "event_completed": {"$ne": "deleted"},
            "booking_price": {"$exists": True},
        }},
        {"$group": {
            "_id": {
                "year": {"$year": "$event_start_datetime"},
                "month": {"$month": "$event_start_datetime"}
            },
            "total_booking_amount": {"$sum": {"$toDouble": "$booking_price"}},
            "total_addon_amount": {"$sum": {"$toDouble": {"$ifNull": ["$add_ons_price", 0]}}},
            "total_cake_spent": {"$sum": {"$toDouble": {"$ifNull": ["$cake_price", 0]}}}
        }}
    ]
    appointment_data = list(appointments_collection.aggregate(appointment_pipeline))

    # 2. Spent: Salary and Expense separation
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

    # 3. Merge All
    summary = {}

    # Appointments
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

    # Spents
    for item in spent_data:
        m, y = item["_id"].get("month"), item["_id"].get("year")
        if m is None or y is None: continue
        key = f"{m:02d}-{y}"
        if key not in summary:
            summary[key] = {
                "booking": 0,
                "addon": 0,
                "cake": 0,
                "salary": 0,
                "expense": 0
            }
        summary[key]["salary"] += item.get("total_salary", 0)
        summary[key]["expense"] += item.get("total_expense", 0)

    # 4. Final Output
    final = []
    total_booking = total_addon = total_cake = total_salary = total_expense = 0

    def sort_key(k): m, y = map(int, k.split("-")); return y, m

    for month in sorted(summary.keys(), key=sort_key):
        data = summary[month]
        booking = data["booking"]
        addon = data["addon"]
        cake = data["cake"]
        salary = data["salary"]
        expense = data["expense"]
        total_income = booking + addon
        amount_spent = salary + expense
        left = total_income - amount_spent

        total_booking += booking
        total_addon += addon
        total_cake += cake
        total_salary += salary
        total_expense += expense

        final.append({
            "month": month,
            "total_booking_amount": round(booking, 2),
            "total_addon_amount": round(addon, 2),
            "total_income": round(total_income, 2),
            "amount_spent_on_salary": round(salary, 2),
            "total_expense": round(expense, 2),
            "amount_spent": round(amount_spent, 2),
            "total_spent_on_cake": round(cake, 2),
            "amount_left": round(left, 2)
        })

    return {
        "monthly_summary": final,
        "total_booking_amount": round(total_booking, 2),
        "total_addon_amount": round(total_addon, 2),
        "total_income": round(total_booking + total_addon, 2),
        "total_spent_on_salary": round(total_salary, 2),
        "total_expense": round(total_expense, 2),
        "total_spent": round(total_salary + total_expense, 2),
        "total_spent_on_cake": round(total_cake, 2),
        "total_left": round((total_booking + total_addon) - (total_salary + total_expense), 2)
    }
