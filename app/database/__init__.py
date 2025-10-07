from app.database.connection import engine, Base, get_db, SessionLocal
# Import models for SQLAlchemy to detect them
from app.models.users import User
from app.models.journal import (
    Faculty,
    Group,
    Subject,
    SubjectGroup,
    Grade,
    Attendance
)

# Note: Tables are created in app/main.py
