from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Boolean, JSON, Text
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


class Challenge(Base):
    __tablename__ = "challenges"
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    base_points = Column(Integer, nullable=False, default=10)
    tags = Column(JSON, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    is_team_challenge = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ChallengeParticipation(Base):
    __tablename__ = "challenge_participation"
    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(String, ForeignKey("challenges.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    status = Column(String, default="completed")
    points_awarded = Column(Integer, default=0)
    evidence = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


