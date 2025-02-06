from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String


# Enum for user roles
class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    LIBRARY_MANAGER = "library_manager"
    READER = "reader"

# User model
class User(SQLModel, table=True):
    __tablename__ = "user"
    user_id: int = Field(default=None, primary_key=True, index=True)  # Auto-increment integer
    username: str = Field(unique=True)
    email: str
    create_at: datetime = Field(default_factory=datetime.utcnow)  # Auto-generate creation timestamp
    updated_at: datetime = Field(default_factory=datetime.utcnow)  # Auto-generate update timestamp
    password: str
    role: UserRole = Field(default=UserRole.READER)  # Default role set to READER

# Book model
class Book(SQLModel, table=True):
    __tablename__ = "book"
    book_id: int = Field(default=None, primary_key=True, index=True)
    book_name: str
    price: float
    is_deleted: bool = Field(default=False)
    is_available: bool = Field(default=True)
    author_name: Optional[str] = Field(sa_column=Column(String(255), nullable=True))

# Assignment model
class Assignment(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.user_id", primary_key=True)
    book_id: int = Field(foreign_key="book.book_id", primary_key=True)
    receive_date: datetime
    submitted_date: datetime= Field(default=None, nullable=True)
    expiry_date:datetime
