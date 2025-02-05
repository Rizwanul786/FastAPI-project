from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Get DATABASE_URL from the environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Database Configuration
engine = create_engine(DATABASE_URL, echo=True)

# Create tables if they don't exist
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Dependency to get DB session
def get_session():
    with Session(engine) as session:
        yield session

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)

# Dependency to get the database session
def get_db():
    db: Session = SessionLocal()
    try:
        yield db  # Return the session
    finally:
        db.close()