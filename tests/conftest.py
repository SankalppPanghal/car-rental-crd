import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool # NEW: Import StaticPool
from src.models import Base, Vehicle, User

# Use an in-memory SQLite database for blazing-fast tests
# 1. 'file:memdb1?mode=memory&cache=shared' forces all threads to look at the same data.
# 2. 'check_same_thread': False allows SQLite to be accessed across multiple threads.
# 3. poolclass=StaticPool keeps the single connection open for all threads to share.
engine = create_engine(
    "sqlite:///file:memdb1?mode=memory&cache=shared",
    connect_args={
        'check_same_thread': False,
        'isolation_level': 'EXCLUSIVE' # <-- ADD THIS: Forces strict locking in SQLite
    },
    poolclass=StaticPool,
    echo=False
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def sample_vehicle(db_session):
    vehicle = Vehicle(
        car_type="SUV",
        make_name="Toyota",
        model_name="RAV4",
        day_rate=100.0,
        hourly_rate=10.0,
        is_available=True
    )
    db_session.add(vehicle)
    db_session.commit()
    db_session.refresh(vehicle)
    return vehicle

@pytest.fixture()
def sample_user(db_session):
    user = User(email="test@example.com", name="John Doe", phone_no="1234567890")
    db_session.add(user)
    db_session.commit()
    return user