# project_tracker_backend/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime

# Base Schemas (for creating/updating)
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "To Do"
    due_date: Optional[date] = None
    project_id: int
    assigned_to: Optional[int] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[date] = None
    assigned_to: Optional[int] = None # Can be set to null by passing None

# Response Schemas (for returning data)
class UserInDB(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    class Config:
        orm_mode = True # Enables ORM mode for SQLAlchemy integration

class ProjectInDB(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_by: int
    created_at: datetime
    # Nested Pydantic model for creator details. Make sure UserInDB has orm_mode = True
    creator: UserInDB

    class Config:
        orm_mode = True

class TaskInDB(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    due_date: Optional[date]
    project_id: int
    assigned_to: Optional[int]
    created_by: int
    created_at: datetime
    # Nested Pydantic models for related objects
    project: ProjectInDB
    assignee: Optional[UserInDB]
    creator: UserInDB

    class Config:
        orm_mode = True

# Token schema for authentication
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None