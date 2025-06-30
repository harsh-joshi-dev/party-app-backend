from fastapi import APIRouter
from config.database import appointments_collection, spents_collection

router = APIRouter()

@router.get("/financial-summary")
async def financial_summary(company_id: str):
    # ———— 1. Appointments: booking + addons (exclude cake) ————
    appointment_pipeline = [
        {"$match": {
            "company_id": company_id,
            "event_completed": {"$ne": "deleted"},
            "event_start_datetime": {"$exists": True}
        }},
        {"$addFields": {
            "booking_amount": {"$toDouble": "$booking_amount"},
            "addon_total": {
                "$sum": {
                    "$map": {
                        "input": {"$ifNull": ["$tags", []]},
                        "as": "t",
                        "in": {"$toDouble": {"$ifNull": ["$$t.price", 0]}}
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
            "total_cake": {"$sum": {"$toDouble": {"$ifNull": ["$cake_price", 0]}}}
        }}
    ]
    appointment_data = list(appointments_collection.aggregate(appointment_pipeline))

    # ———— 2. Spents: salary and expense with correct date fields ————
    spent_pipeline = [
        {"$match": {"company_id": company_id}},
        {"$addFields": {
            "aggregation_date": {
                "$cond": [
                    {"$eq": ["$type", "Salary"]},
                    "$salary_given_date",
                    "$bought_date"
                ]
            }
        }},
        {"$group": {
            "_id": {
                "year": {"$year": "$aggregation_date"},
                "month": {"$month": "$aggregation_date"}
            },
            "amount_spent_on_salary": {
                "$sum": {
                    "$cond": [{"$eq": ["$type", "Salary"]}, {"$toDouble": {"$ifNull": ["$amount", 0]}}, 0]
                }
            },
            "total_expense": {
                "$sum": {
                    "$cond": [{"$eq": ["$type", "Expense"]}, {"$toDouble": {"$ifNull": ["$amount", 0]}}, 0]
                }
            }
        }}
    ]
    spent_data = list(spents_collection.aggregate(spent_pipeline))

    # ———— 3. Merge both by month ————
    summary = {}

    for a in appointment_data:
        m, y = a["_id"]["month"], a["_id"]["year"]
        key = f"{m:02d}-{y}"
        summary[key] = {
            "total_booking_amount": a["total_booking_amount"],
            "total_addon_amount": a["total_addon_amount"],
            "total_spent_on_cake": a.get("total_cake", 0),
            "amount_spent_on_salary": 0,
            "total_expense": 0
        }

    for s in spent_data:
        m, y = s["_id"]["month"], s["_id"]["year"]
        key = f"{m:02d}-{y}"
        if key not in summary:
            summary[key] = {
                "total_booking_amount": 0,
                "total_addon_amount": 0,
                "total_spent_on_cake": 0,
                "amount_spent_on_salary": 0,
                "total_expense": 0
            }
        summary[key]["amount_spent_on_salary"] = s.get("amount_spent_on_salary", 0)
        summary[key]["total_expense"] = s.get("total_expense", 0)

    # ———— 4. Build final monthly summary and totals ————
    final = []
    tot_b = tot_a = tot_sal = tot_exp = tot_cake = 0

    def sort_key(key):  # For proper sorting like "06-2025", "07-2025"
        m, y = map(int, key.split("-"))
        return y, m

    for key in sorted(summary.keys(), key=sort_key):
        d = summary[key]
        income = d["total_booking_amount"] + d["total_addon_amount"]
        spent = d["amount_spent_on_salary"] + d["total_expense"]
        left = income - spent

        tot_b += d["total_booking_amount"]
        tot_a += d["total_addon_amount"]
        tot_sal += d["amount_spent_on_salary"]
        tot_exp += d["total_expense"]
        tot_cake += d["total_spent_on_cake"]

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

    # ———— 5. Final response ————
    return {
        "monthly_summary": final,
        "total_booking_amount": round(tot_b, 2),
        "total_addon_amount": round(tot_a, 2),
        "total_income": round(tot_b + tot_a, 2),
        "total_spent_on_salary": round(tot_sal, 2),
        "total_expense": round(tot_exp, 2),
        "total_spent": round(tot_sal + tot_exp, 2),
        "total_spent_on_cake": round(tot_cake, 2),
        "total_left": round((tot_b + tot_a) - (tot_sal + tot_exp), 2)
    }
