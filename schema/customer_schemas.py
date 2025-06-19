def individual_customer_serial(customer) -> dict:
    return {
        "id": str(customer["_id"]),
        "full_name": customer.get("full_name"),
        "caste": customer.get("caste"),
        "contact_number": customer.get("contact_number"),
        "preferred_bhk": customer.get("preferred_bhk"),
        "residential_property_type": customer.get("residential_property_type"),
        "commercial_property_type": customer.get("commercial_property_type"),
        "budget_min": customer.get("budget_min"),
        "budget_max": customer.get("budget_max"),
        "special_requirements": customer.get("special_requirements"),
        "preferred_area": customer.get("preferred_area"),
        "intent": customer.get("intent"),
        "property_condition": customer.get("property_condition"),
        "furnished_status": customer.get("furnished_status"),
        "parking_options": customer.get("parking_options"),
        "preferred_tenant_type": customer.get("preferred_tenant_type"),
        "family_members_count": customer.get("family_members_count"),
        "city_name": customer.get("city_name"),
        "waiting_period": customer.get("waiting_period"),
        "created_by": customer.get("created_by"),
        "assigned_to": customer.get("assigned_to"),
        "lead_source": customer.get("lead_source"),
        "status": customer.get("status"),
        "added_on": str(customer.get("added_on"))
    }

def list_customer_serial(customers) -> list:
    return [individual_customer_serial(c) for c in customers]
