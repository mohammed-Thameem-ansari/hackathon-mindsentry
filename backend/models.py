"""
File: models.py
Purpose: Defines database models using SQLAlchemy.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)  # Renamed from uid to id
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)  # Store hashed password in production

class Text(Base):
    __tablename__ = "texts"
    id = Column(Integer, primary_key=True, index=True)  # Renamed text_id to id
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Updated ForeignKey
    text = Column(String, nullable=False)
    tscore = Column(Float, nullable=False)  # Sentiment confidence score
    sentiment = Column(String, nullable=False)  # "positive" or "negative"
    label = Column(String, nullable=False)  # "uploaded", "direct_audio", "text"

class Chat(Base):
    __tablename__ = "chat"
    id = Column(Integer, primary_key=True, index=True)
    cscore = Column(Float, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    summary = Column(String, nullable=False)

class Therapy(Base):
    __tablename__ = "therapy"
    id = Column(Integer, primary_key=True, index=True)
    sentiment_score = Column(Float, nullable=False)
    audio = Column(String, nullable=True)
    video = Column(String, nullable=True)
    quotes = Column(String, nullable=True)