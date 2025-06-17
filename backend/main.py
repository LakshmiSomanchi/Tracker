# project_tracker_backend/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from fastapi.middleware.cors import CORSMiddleware # For enabling CORS

from . import models, schemas, crud, auth
from .database import engine, get_db, Base

# Create database tables (this will run when the app starts if they don't exist)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Project Tracker API",
    description="API for managing projects, tasks, and users.",
    version="0.1.0",
)

# CORS configuration - IMPORTANT for Streamlit frontend
# Add origins here. For local development: http://localhost:8501 (Streamlit's default)
# For deployment: you will need to add your Streamlit Cloud app's URL.
origins = [
    "http://localhost",
    "http://localhost:8501",
    "https://tracker.pmu.streamlit.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint for testing
@app.get("/")
def read_root():
    return {"message": "Welcome to the Project Tracker API!"}

# User Authentication
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not crud.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=schemas.UserInDB, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.get("/users/me/", response_model=schemas.UserInDB)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@app.get("/users/", response_model=List[schemas.UserInDB])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
               current_user: models.User = Depends(auth.get_current_user)): # Protected
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

# Project Endpoints
@app.post("/projects/", response_model=schemas.ProjectInDB, status_code=status.HTTP_201_CREATED)
def create_project_endpoint(project: schemas.ProjectCreate, db: Session = Depends(get_db),
                            current_user: models.User = Depends(auth.get_current_user)):
    return crud.create_project(db=db, project=project, user_id=current_user.id)

@app.get("/projects/", response_model=List[schemas.ProjectInDB])
def read_projects_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                           current_user: models.User = Depends(auth.get_current_user)):
    projects = crud.get_projects(db, skip=skip, limit=limit)
    return projects

@app.get("/projects/{project_id}", response_model=schemas.ProjectInDB)
def read_project_endpoint(project_id: int, db: Session = Depends(get_db),
                          current_user: models.User = Depends(auth.get_current_user)):
    db_project = crud.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project

@app.put("/projects/{project_id}", response_model=schemas.ProjectInDB)
def update_project_endpoint(project_id: int, project: schemas.ProjectCreate, db: Session = Depends(get_db),
                            current_user: models.User = Depends(auth.get_current_user)):
    db_project = crud.update_project(db, project_id, project)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project

@app.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_endpoint(project_id: int, db: Session = Depends(get_db),
                            current_user: models.User = Depends(auth.get_current_user)):
    if not crud.delete_project(db, project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted successfully"}

# Task Endpoints
@app.post("/tasks/", response_model=schemas.TaskInDB, status_code=status.HTTP_201_CREATED)
def create_task_endpoint(task: schemas.TaskCreate, db: Session = Depends(get_db),
                         current_user: models.User = Depends(auth.get_current_user)):
    # Check if project exists
    db_project = crud.get_project(db, task.project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    # Check if assigned_to user exists
    if task.assigned_to and not crud.get_user(db, task.assigned_to):
        raise HTTPException(status_code=404, detail="Assigned user not found")

    return crud.create_task(db=db, task=task, created_by_user_id=current_user.id)

@app.get("/tasks/", response_model=List[schemas.TaskInDB])
def read_all_tasks_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                            current_user: models.User = Depends(auth.get_current_user)):
    tasks = crud.get_all_tasks(db, skip=skip, limit=limit)
    return tasks

@app.get("/tasks/project/{project_id}", response_model=List[schemas.TaskInDB])
def read_tasks_by_project_endpoint(project_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                                   current_user: models.User = Depends(auth.get_current_user)):
    db_project = crud.get_project(db, project_id=project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    tasks = crud.get_tasks_by_project(db, project_id=project_id, skip=skip, limit=limit)
    return tasks

@app.get("/tasks/{task_id}", response_model=schemas.TaskInDB)
def read_task_endpoint(task_id: int, db: Session = Depends(get_db),
                       current_user: models.User = Depends(auth.get_current_user)):
    db_task = crud.get_task(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@app.put("/tasks/{task_id}", response_model=schemas.TaskInDB)
def update_task_endpoint(task_id: int, task: schemas.TaskUpdate, db: Session = Depends(get_db),
                         current_user: models.User = Depends(auth.get_current_user)):
    db_task = crud.update_task(db, task_id, task)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_endpoint(task_id: int, db: Session = Depends(get_db),
                         current_user: models.User = Depends(auth.get_current_user)):
    if not crud.delete_task(db, task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}