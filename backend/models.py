# project_tracker_backend/models.py
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=func.now())

    projects = relationship("Project", back_populates="creator")
    created_tasks = relationship("Task", foreign_keys="[Task.created_by]", back_populates="creator")
    assigned_tasks = relationship("Task", foreign_keys="[Task.assigned_to]", back_populates="assignee")

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())

    creator = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan") # cascade for deleting tasks with project

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text)
    status = Column(String, default="To Do", nullable=False) # e.g., 'To Do', 'In Progress', 'Done', 'Blocked'
    due_date = Column(Date)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())

    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", foreign_keys="[Task.assigned_to]", back_populates="assigned_tasks")
    creator = relationship("User", foreign_keys="[Task.created_by]", back_populates="created_tasks")