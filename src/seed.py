import random
from sqlalchemy.orm import Session
from src.models import Vehicle, User

# Sample automotive data for realistic generation
MAKES_AND_MODELS = {
    "Sedan": [("Toyota", "Camry"), ("Honda", "Civic"), ("BMW", "3 Series"), ("Hyundai", "Elantra")],
    "SUV": [("Toyota", "RAV4"), ("Ford", "Explorer"), ("Jeep", "Grand Cherokee"), ("Volvo", "XC90")],
    "Van": [("Honda", "Odyssey"), ("Chrysler", "Pacificia"), ("Ford", "Transit"), ("Mercedes", "Sprinter")]
}

def seed_mock_data(db_session: Session, num_vehicles: int = 20, num_users: int = 5):
    """Populates the database with randomized vehicles and standardized mock users."""
    
    # 1. Seed Users
    users = []
    for i in range(num_users):
        user = User(
            email=f"customer_{i}@example.com",
            name=f"User No {i}",
            phone_no=f"+1555010{i}"
        )
        db_session.add(user)
        users.append(user)

    # 2. Seed Vehicles with randomized categories and rates
    car_types = ["Sedan", "SUV", "Van"]
    for _ in range(num_vehicles):
        c_type = random.choice(car_types)
        make, model = random.choice(MAKES_AND_MODELS[c_type])
        
        # Structure pricing dynamically based on type premium
        base_rate = {"Sedan": 40.0, "SUV": 80.0, "Van": 110.0}[c_type]
        day_rate = round(base_rate + random.uniform(10.0, 40.0), 2)
        hourly_rate = round((day_rate / 24) * 1.5, 2)  # Hourly premium rate

        vehicle = Vehicle(
            car_type=c_type,
            make_name=make,
            model_name=model,
            day_rate=day_rate,
            hourly_rate=hourly_rate,
            is_available=True
        )
        db_session.add(vehicle)

    db_session.commit()
    print(f"Successfully seeded {num_users} users and {num_vehicles} randomized vehicles.")