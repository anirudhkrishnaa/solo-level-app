# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base # Import the Base from your models file

# The database URL. For SQLite, this is the path to the database file.
# It will create a file named 'sololevel.db' in your project directory.
DATABASE_URL = "sqlite:///./sololevel.db"

# The engine is the main entry point to the database.
# The 'check_same_thread' argument is needed only for SQLite.
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# A SessionLocal class is a factory for creating new database sessions.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_db_and_tables():
    """
    Creates the database file and all tables defined in models.py.
    Call this function once at the start of your application.
    """
    print("Creating database and tables...")
    Base.metadata.create_all(bind=engine)
    print("Database and tables created successfully.")
