def individual_user_serial(user) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "phone": user["phone"],
        "email": user.get("email"),
        "user_type": user.get("user_type"),
        "preferred_location": user.get("preferred_location"),
        "created_at": user.get("created_at")
    }

def list_user_serial(users) -> list:
    return [individual_user_serial(user) for user in users]
