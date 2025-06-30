from fastapi import APIRouter
from config.database import appointments_collection, spents_collection

router = APIRouter()

@router.get("/financial-summary")
async def financial_summary(company_id: str):
    # 1. Aggregate Appointments
    appointment_pipeline = [
        {"$match": {
            "company_id": company_id,
            "event_completed": {"$ne": "deleted"},
            "event_start_datetime": {"$exists": True}
        }},
        {"$addFields": {
            "booking_amount": {"$toDouble": {"$ifNull": ["$booking_amount", 0]}},
            "addon_total": {
                "$sum": {
                    "$map": {
                        "input": {"$ifNull": ["$tags", []]},
                        "as": "t",
                        "in": {"$toDouble": {"$ifNull": ["$$t.price", 0]}}
                    }
                }
            },
            "cake_price": {"$toDouble": {"$ifNull": ["$cake_price", 0]}}
        }},
        {"$group": {
            "_id": {
                "year": {"$year": "$event_start_datetime"},
                "month": {"$month": "$event_start_datetime"}
            },
            "total_booking_amount": {"$sum": "$booking_amount"},
            "total_addon_amount": {"$sum": "$addon_total"},
            "total_spent_on_cake": {"$sum": "$cake_price"}
        }}
    ]
    appointment_data = list(appointments_collection.aggregate(appointment_pipeline))

    # 2. Aggregate Spents (handle null dates safely)
    spent_pipeline = [
        {"$match": {
            "company_id": company_id,
            "$or": [
                {"salary_given_date": {"$ne": None}},
                {"bought_date": {"$ne": None}}
            ]
        }},
        {"$addFields": {
            "aggregation_date": {
                "$cond": [
                    {"$and": [{"$eq": ["$type", "Salary"]}, {"$ne": ["$salary_given_date", None]}]},
                    "$salary_given_date",
                    "$bought_date"
                ]
            },
            "safe_amount": {"$toDouble": {"$ifNull": ["$amount", 0]}}
        }},
        {"$group": {
            "_id": {
                "year": {"$year": "$aggregation_date"},
                "month": {"$month": "$aggregation_date"}
            },
            "amount_spent_on_salary": {
                "$sum": {"$cond": [{"$eq": ["$type", "Salary"]}, "$safe_amount", 0]}
            },
            "total_expense": {
                "$sum": {"$cond": [{"$eq": ["$type", "Expense"]}, "$safe_amount", 0]}
            }
        }}
    ]
    spent_data = list(spents_collection.aggregate(spent_pipeline))

    # 3. Merge monthly data
    summary = {}

    for a in appointment_data:
        key = f"{a['_id']['month']:02d}-{a['_id']['year']}"
        summary[key] = {
            "total_booking_amount": a.get("total_booking_amount", 0),
            "total_addon_amount": a.get("total_addon_amount", 0),
            "total_spent_on_cake": a.get("total_spent_on_cake", 0),
            "amount_spent_on_salary": 0,
            "total_expense": 0
        }

    for s in spent_data:
        key = f"{s['_id']['month']:02d}-{s['_id']['year']}"
        if key not in summary:
            summary[key] = {
                "total_booking_amount": 0,
                "total_addon_amount": 0,
                "total_spent_on_cake": 0,
                "amount_spent_on_salary": 0,
                "total_expense": 0
            }
        summary[key]["amount_spent_on_salary"] += s.get("amount_spent_on_salary", 0)
        summary[key]["total_expense"] += s.get("total_expense", 0)

    # 4. Final Compilation
    final = []
    total_booking = total_addon = total_salary = total_expense = total_cake = 0

    def sort_key(k):
        m, y = map(int, k.split('-'))
        return y, m

    for key in sorted(summary.keys(), key=sort_key):
        d = summary[key]
        income = d["total_booking_amount"] + d["total_addon_amount"]
        spent = d["amount_spent_on_salary"] + d["total_expense"]
        left = income - spent

        final.append({
            "month": key,
            "total_booking_amount": round(d["total_booking_amount"], 2),
            "total_addon_amount": round(d["total_addon_amount"], 2),
            "total_income": round(income, 2),
            "amount_spent_on_salary": round(d["amount_spent_on_salary"], 2),
            "total_expense": round(d["total_expense"], 2),
            "amount_spent": round(spent, 2),
            "total_spent_on_cake": round(d["total_spent_on_cake"], 2),
            "amount_left": round(left, 2)
        })

        total_booking += d["total_booking_amount"]
        total_addon += d["total_addon_amount"]
        total_salary += d["amount_spent_on_salary"]
        total_expense += d["total_expense"]
        total_cake += d["total_spent_on_cake"]

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
