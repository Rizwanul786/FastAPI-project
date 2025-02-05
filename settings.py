from fastapi import FastAPI
from database import create_db_and_tables
from routes import users, books, assignments
from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "mysql+mysqlconnector://root:Password@101@localhost/Library_management"
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Include routers
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(books.router, prefix="/books", tags=["Books"])
app.include_router(assignments.router, prefix="/assignments", tags=["Assignments"])
