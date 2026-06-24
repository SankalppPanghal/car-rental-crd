import pytest
from datetime import datetime, timedelta
from src.services import calculate_cost, check_availability, create_reservation
from src.models import Reservation
from src.models import Vehicle

def test_calculate_cost_exact_days(sample_vehicle):
    # Trivial Case: Exactly 2 days
    start = datetime(2026, 7, 1, 10, 0)
    end = datetime(2026, 7, 3, 10, 0)
    cost = calculate_cost(sample_vehicle, start, end)
    assert cost == 200.0 # 2 days * $100

def test_calculate_cost_with_extra_hours(sample_vehicle):
    # Basic Case: 1 day and 4 hours
    start = datetime(2026, 7, 1, 10, 0)
    end = datetime(2026, 7, 2, 14, 0)
    cost = calculate_cost(sample_vehicle, start, end)
    assert cost == 140.0 # (1 * $100) + (4 * $10)

def test_calculate_cost_rounds_up_minutes(sample_vehicle):
    # Edge Case: 1 day, 2 hours, and 15 minutes should charge for 3 hours
    start = datetime(2026, 7, 1, 10, 0)
    end = datetime(2026, 7, 2, 12, 15)
    cost = calculate_cost(sample_vehicle, start, end)
    assert cost == 130.0 # (1 * $100) + (3 * $10)

def test_availability_no_conflict(db_session, sample_vehicle):
    # Trivial Case: Car has no reservations
    start = datetime(2026, 7, 1, 10, 0)
    end = datetime(2026, 7, 3, 10, 0)
    
    available_cars = check_availability(db_session, start, end)
    assert len(available_cars) == 1
    assert available_cars[0].id == sample_vehicle.id

def test_availability_3_hour_buffer_conflict(db_session, sample_user, sample_vehicle):
    # Basic Case: Existing reservation from 10:00 AM to 2:00 PM
    existing_res_start = datetime(2026, 7, 1, 10, 0)
    existing_res_end = datetime(2026, 7, 1, 14, 0)
    create_reservation(db_session, sample_user.email, sample_vehicle.id, existing_res_start, existing_res_end)

    # Attempt 1: Try to book at 4:00 PM (Only 2 hours after drop-off) -> Should Fail
    new_start_fail = datetime(2026, 7, 1, 16, 0)
    new_end_fail = datetime(2026, 7, 1, 20, 0)
    assert len(check_availability(db_session, new_start_fail, new_end_fail)) == 0

    # Attempt 2: Try to book at 5:00 PM (Exactly 3 hours after drop-off) -> Should Pass
    new_start_pass = datetime(2026, 7, 1, 17, 0)
    new_end_pass = datetime(2026, 7, 1, 20, 0)
    assert len(check_availability(db_session, new_start_pass, new_end_pass)) == 1

def test_availability_search_all_types(db_session):
    """Proves that querying without a car_type returns the entire available fleet."""
    # 1. Seed the database with a mixed fleet
    sedan = Vehicle(car_type="Sedan", make_name="Toyota", model_name="Camry", day_rate=50, hourly_rate=5, is_available=True)
    suv = Vehicle(car_type="SUV", make_name="Ford", model_name="Explorer", day_rate=80, hourly_rate=8, is_available=True)
    db_session.add_all([sedan, suv])
    db_session.commit()

    start = datetime(2026, 10, 1, 10, 0)
    end = datetime(2026, 10, 2, 10, 0)

    # 2. Query with NO car type specified
    available_cars = check_availability(db_session, start, end)
    
    # 3. Assert both cars are returned
    assert len(available_cars) == 2
    returned_types = {car.car_type for car in available_cars}
    assert "Sedan" in returned_types
    assert "SUV" in returned_types

def test_availability_search_by_specific_type(db_session):
    """Proves that providing a car_type correctly filters the results."""
    # 1. Seed the database with a mixed fleet
    sedan = Vehicle(car_type="Sedan", make_name="Honda", model_name="Civic", day_rate=50, hourly_rate=5, is_available=True)
    suv = Vehicle(car_type="SUV", make_name="Jeep", model_name="Wrangler", day_rate=80, hourly_rate=8, is_available=True)
    db_session.add_all([sedan, suv])
    db_session.commit()

    start = datetime(2026, 11, 1, 10, 0)
    end = datetime(2026, 11, 2, 10, 0)

    # 2. Query specifically for SUVs
    available_suvs = check_availability(db_session, start, end, car_type="SUV")
    
    # 3. Assert only the SUV is returned
    assert len(available_suvs) == 1
    assert available_suvs[0].car_type == "SUV"

    # 4. Query for a type that doesn't exist in the available inventory
    available_vans = check_availability(db_session, start, end, car_type="Van")
    assert len(available_vans) == 0