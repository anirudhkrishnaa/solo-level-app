# C:/Anirudh/solo-level/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from models import Base # Import the Base from your models file

# The database URL. For SQLite, this is the path to the database file.
DATABASE_URL = "sqlite:///./sololevel.db"

# The engine is the main entry point to the database.
# The 'check_same_thread' argument is needed only for SQLite.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    # echo=True # Uncomment for debugging to see generated SQL
)

# A SessionLocal class is a factory for creating new database sessions.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_db_and_tables():
    """
    Creates the database file and all tables defined in models.py.
    Call this function once at the start of your application.
    """
    print("Creating database and tables...")
    # This is idempotent; it won't re-create existing tables.
    Base.metadata.create_all(bind=engine)
    print("Database and tables created successfully.")

@contextmanager
def get_db():
    """
    Provides a transactional scope around a series of operations.
    This is a robust pattern for session management.
    Usage:
        with get_db() as db:
            db.query(...)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
