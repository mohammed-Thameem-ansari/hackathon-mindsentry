"""
File: database.py
Purpose: Sets up the SQLite database connection and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "sqlite:///mindsentry.db"  # SQLite database file
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})  # SQLite concurrency fix
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()