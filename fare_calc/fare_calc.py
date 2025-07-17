# fare_calculator.py

def calculate_fare(ticket_type: str, travel_class: str, distance_km: int) -> float:
    base_fare = {
        "standard": 0.5,
        "first_class": 1.0
    }

    class_multiplier = {
        "economy": 1.0,
        "business": 1.5
    }

    if ticket_type not in base_fare:
        raise ValueError(f"Invalid ticket_type: {ticket_type}")
    
    if travel_class not in class_multiplier:
        raise ValueError(f"Invalid travel_class: {travel_class}")
    
    if distance_km <= 0:
        raise ValueError(f"Invalid distance: {distance_km} km")

    return base_fare[ticket_type] * class_multiplier[travel_class] * distance_km
