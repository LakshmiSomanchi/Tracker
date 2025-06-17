# project_tracker_backend/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Read from environment variable. Provide a fallback for local testing if env var not set.
# This value will be overridden by Gitpod's .gitpod.yml and Render's environment variables.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/default_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()