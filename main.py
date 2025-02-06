from logging import log
from fastapi import FastAPI, Depends,Body, Form
from pydantic import BaseModel
from typing import List
from datetime import timedelta,datetime
from sqlmodel import Session
from fastapi import HTTPException,status
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext

from db_config import create_db_and_tables, get_session,get_db  # Import database setup
from models import User, Book, Assignment,UserRole  # Import your models
from auth import create_access_token,verify_password,get_current_user

# Password encryption setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Encrypt the password using bcrypt."""
    return pwd_context.hash(password)

# Create FastAPI app
app = FastAPI()


# Create tables on startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Create an User
@app.post("/users/", response_model=User)
def create_user(user: User, session: Session = Depends(get_session)):
    # Remove role if it exists
    user_dict = user.dict()  # Convert SQLModel instance to a dictionary
    user_dict.pop("role", None)  # Remove role safely if it exists
    user_dict["password"] = hash_password(user_dict["password"])
    user = User(**user_dict) # Create a new User instance without role
    try:
        session.add(user)      # Add user object to session
        session.commit()       # Commit transaction (save to DB)
        session.refresh(user)  # Reload user from DB with updated values
        return user
    except Exception as e:  # Catch any other unexpected errors
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# Login route to generate JWT token
class Token(BaseModel):
    access_token: str
    token_type: str

class AssignmentBody(BaseModel):
    user_id: int
    author_name: str
    book_name: str

# Login user
@app.post("/login", response_model=Token)
def login(username: str = Body(None) or Form(None),password: str = Body(None) or Form(None), db: Session = Depends(get_db)):
    print("===>>",username)
    user = db.query(User).filter(User.username == username).first()
    # Check if the user exists and if the password matches
    if not user or not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Create JWT token
    token_expires = timedelta(minutes=30)
    token = create_access_token(data={"sub": user.username}, expires_delta=token_expires)

    return {"access_token": token, "token_type": "bearer"}


@app.get("/get_all_users/", response_model=List[User])
def read_users(session: Session = Depends(get_session)):
    return session.query(User).all()

# Book Endpoints
@app.post("/add_book/", response_model=Book)
def create_book(book: Book, session: Session = Depends(get_session),user: User = Depends(get_current_user)):
    # Check if the user has an admin role
    if user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Access denied: Admins only")

    session.add(book)
    session.commit()
    session.refresh(book)
    return book

@app.get("/books/", response_model=List[Book])
def read_books(session: Session = Depends(get_session)):
    return session.query(Book).all()


@app.post("/assign_book/", response_model=Assignment)
def assign_book(assignment: AssignmentBody, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    print("===>>>>",dict(assignment))
    if user.role != UserRole.LIBRARY_MANAGER:
        raise HTTPException(status_code=403, detail="Access denied: Only Library Managers can assign books")

    # Query the book based on book_name and author_name from the request body
    book = session.query(Book).filter(
        Book.book_name == assignment.book_name,  # Filter by book_name from the request body
        Book.author_name == assignment.author_name,  # Filter by author_name from the request body
        Book.is_available == True,  # Ensure the book is available
        Book.is_deleted==False
    ).first()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Query the user to assign the book
    assign_user = session.query(User).filter(User.user_id == assignment.user_id).first()
    if not assign_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Set expiry date for the assignment (10 days)
    expiry_date = datetime.today() + timedelta(days=10)

    # Create the Assignment object
    new_assignment = Assignment(
        user_id=assign_user.user_id,  # Use user ID
        book_id=book.book_id,  # Use book ID
        expiry_date=expiry_date,
        receive_date=datetime.today()  # Set the current date as receive date
    )

    # Update the book's availability
    book.is_available = False
    session.add(book)  # Update book status

    # Add the new assignment
    session.add(new_assignment)
    session.commit()
    session.refresh(new_assignment)
    return new_assignment

@app.post("/submit_book/", response_model=Assignment)
def submit_book(assignment: Assignment, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    if user.role != UserRole.LIBRARY_MANAGER:
        raise HTTPException(status_code=403, detail="Access denied: Only Library Managers can mark book submissions")

    # Find the book by ID
    book = session.query(Book).filter(Book.book_id == assignment.book_id).first()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Find the assignment entry for this book
    assign = session.query(Assignment).filter(Assignment.book_id == assignment.book_id, Assignment.user_id == assignment.user_id).first()

    if not assign:
        raise HTTPException(status_code=404, detail="Assignment record not found")

    book.is_available = True

    assign.submitted_date = datetime.today()

    session.add(book)
    session.add(assign)
    session.commit()
    session.refresh(assign)

    return assign


@app.get("/all_assignments/", response_model=List[Assignment])
def read_assignments(session: Session = Depends(get_session)):
    return session.query(Assignment).all()

@app.put("/delete_book/", response_model=Book)
def read_assignments(book:Book,session: Session = Depends(get_session),user: User = Depends(get_current_user)):
    # Query the book based on book_name and author_name from the request body
    if user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Access denied: Admins only allow to delete a book")
    book = session.query(Book).filter(
        Book.book_id == book.book_id,
    ).first()
    book.is_deleted = True
    session.add(book)
    session.commit()
    session.refresh(book)
    return book

# Root Endpoint
@app.get("/")
def root():
    return {"message": "Welcome to the Library Management API"}
