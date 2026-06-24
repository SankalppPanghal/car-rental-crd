import uuid
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.types import Uuid
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    email = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone_no = Column(String, nullable=False)

class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    car_type = Column(String, nullable=False) # Simplified from Enum for SQLite test compatibility
    make_name = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    day_rate = Column(Float, nullable=False)
    hourly_rate = Column(Float, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)

class Reservation(Base):
    __tablename__ = "reservations"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_email = Column(String, ForeignKey("users.email"), nullable=False)
    vehicle_id = Column(Uuid, ForeignKey("vehicles.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    total_cost = Column(Float, nullable=False)