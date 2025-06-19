def individual_property_serial(property) -> dict:
    return {
        "id": str(property["_id"]),
        "property_title": property.get("property_title"),
        "condition": property.get("condition"),
        "category": property.get("category"),
        "square_feet": property.get("square_feet"),
        "rate": property.get("rate"),
        "location": property.get("location"),
        "furnishing_status": property.get("furnishing_status"),
        "parking_options": property.get("parking_options"),
        "parking_capacity": property.get("parking_capacity"),
        "allowed_for": property.get("allowed_for"),
        "family_members_allowed": property.get("family_members_allowed"),
        "availability_status": property.get("availability_status"),
        "listed_by": property.get("listed_by"),
        "created_by": property.get("created_by"),
        "created_at": str(property.get("created_at")),
        "updated_at": str(property.get("updated_at")) if property.get("updated_at") else None
    }

def list_property_serial(properties) -> list:
    return [individual_property_serial(p) for p in properties]
