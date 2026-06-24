from datetime import datetime, timedelta
from sqlalchemy import and_
from sqlalchemy.orm import Session
from src.models import Vehicle, Reservation

def calculate_cost(vehicle: Vehicle, start_time: datetime, end_time: datetime) -> float:
    duration = end_time - start_time
    days = duration.days
    
    remaining_seconds = duration.seconds
    hours = remaining_seconds // 3600
    
    # If there are any leftover minutes/seconds, charge for an additional hour
    if remaining_seconds % 3600 > 0:
        hours += 1 

    return (days * vehicle.day_rate) + (hours * vehicle.hourly_rate)


def check_availability(db_session: Session, requested_start: datetime, requested_end: datetime, car_type: str = None):
    # Add the mandatory 3-hour buffer
    check_start = requested_start - timedelta(hours=3)
    check_end = requested_end + timedelta(hours=3)

    # Find IDs of vehicles that have conflicting reservations
    overlapping_reservations = db_session.query(Reservation.vehicle_id).filter(
        and_(
            Reservation.start_time < check_end,
            Reservation.end_time > check_start
        )
    ).scalar_subquery()

    # Query for vehicles not in the conflicting list
    query = db_session.query(Vehicle).filter(
        Vehicle.is_available == True,
        Vehicle.id.not_in(overlapping_reservations)
    )

    if car_type:
        query = query.filter(Vehicle.car_type == car_type)

    return query.all()


def create_reservation(db_session: Session, email: str, vehicle_id, start_time: datetime, end_time: datetime):
    vehicle = db_session.query(Vehicle).filter(Vehicle.id == vehicle_id).with_for_update().first()
    
    if not vehicle:
        raise ValueError("Vehicle not found")

    cost = calculate_cost(vehicle, start_time, end_time)
    
    new_res = Reservation(
        user_email=email,
        vehicle_id=vehicle_id,
        start_time=start_time,
        end_time=end_time,
        total_cost=cost
    )
    
    db_session.add(new_res)
    db_session.commit()
    db_session.refresh(new_res)
    return new_res