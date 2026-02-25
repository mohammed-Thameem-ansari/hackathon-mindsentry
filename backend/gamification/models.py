from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, JSON, Text
from sqlalchemy.sql import func
from ..database import Base
import enum


class PointsSource(str, enum.Enum):
    steps = "steps"
    challenge = "challenge"
    bonus = "bonus"


class PointsLedger(Base):
    __tablename__ = "points_ledger"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    source = Column(Enum(PointsSource), nullable=False)
    points = Column(Integer, nullable=False)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Streak(Base):
    __tablename__ = "streaks"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    current_streak = Column(Integer, default=0, nullable=False)
    last_action_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Badge(Base):
    __tablename__ = "badges"
    code = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BadgeEarned(Base):
    __tablename__ = "badges_earned"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    badge_code = Column(String, ForeignKey("badges.code"))
    earned_at = Column(DateTime(timezone=True), server_default=func.now())


# Challenge models now live in backend/models.py (Phase 2). This module intentionally
# excludes Challenge/ChallengeParticipation to avoid duplicate table definitions.


