from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os

# Get database URL from environment variable or use default for local development
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/student_journal")

# Create engine - if using SQLite (for local development without Docker)
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # Configure connection pool with larger size and recycle time
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=20,         # Increased from default 5
        max_overflow=20,      # Increased from default 10
        pool_timeout=60,      # Increased from default 30
        pool_recycle=1800     # Recycle connections after 30 minutes
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 