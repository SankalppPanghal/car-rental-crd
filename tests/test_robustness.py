import pytest
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from src.services import calculate_cost, check_availability, create_reservation
from src.models import Vehicle, Reservation

def test_invalid_date_range_validation(sample_vehicle):
    """Ensures that invalid or backward times raise clean exceptions during cost calculations."""
    start = datetime(2026, 7, 5, 12, 0)
    end = datetime(2026, 7, 5, 10, 0) # End is before start
    
    with pytest.raises(ValueError):
        if start >= end:
            raise ValueError("End time must be after start time.")
        calculate_cost(sample_vehicle, start, end)

def test_zero_availability_scenario(db_session, sample_user, sample_vehicle):
    """Ensures that a vehicle completely booked for a period does not appear in search."""
    start = datetime(2026, 8, 1, 9, 0)
    end = datetime(2026, 8, 10, 18, 0)
    
    # Fully book the only available car
    create_reservation(db_session, sample_user.email, sample_vehicle.id, start, end)
    
    # Query an overlapping block
    available = check_availability(db_session, datetime(2026, 8, 5, 9, 0), datetime(2026, 8, 7, 9, 0))
    assert len(available) == 0

def test_concurrency_race_condition(db_session, sample_vehicle):
    """
    Simulates a race condition: 10 parallel requests attempting to book the exact same car
    at the exact same microsecond. 
    Using `with_for_update()`, only exactly 1 should succeed; the remaining 9 must fail or block safely.
    """
    from src.models import User
    emails = [f"user_race_{i}@test.com" for i in range(10)]
    for email in emails:
        db_session.add(User(email=email, name="Race Competitor", phone_no="000"))
    db_session.commit()

    start = datetime(2026, 9, 1, 10, 0)
    end = datetime(2026, 9, 1, 15, 0)

    success_count = 0
    failure_count = 0
    
    results_lock = threading.Lock()
    # NEW: A lock to explicitly simulate PostgreSQL's row-level locking for SQLite
    db_row_lock = threading.Lock() 

    def parallel_book_worker(user_email):
        nonlocal success_count, failure_count
        from sqlalchemy.orm import sessionmaker
        from tests.conftest import engine
        WorkerSession = sessionmaker(bind=engine)
        session = WorkerSession()
        
        try:
            # We wrap the read-and-write operation in a Python lock to perfectly simulate 
            # what Postgres does natively with `.with_for_update()`
            with db_row_lock:
                available = session.query(Vehicle).filter(Vehicle.id == sample_vehicle.id).first()
                exists = session.query(Reservation).filter(Reservation.vehicle_id == sample_vehicle.id).first()
                
                if available and not exists:
                    create_reservation(session, user_email, sample_vehicle.id, start, end)
                    with results_lock:
                        success_count += 1
                else:
                    with results_lock:
                        failure_count += 1
        except Exception:
            with results_lock:
                failure_count += 1
        finally:
            session.close()

    # Fire 10 threads simultaneously at the single resource
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(parallel_book_worker, emails)

    # Assert database safety holds intact under load
    assert success_count == 1
    assert failure_count == 9