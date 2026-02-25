from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class LeaderboardEntry(BaseModel):
    user_id: int
    username: str
    total_steps: int
    total_points: Optional[int] = 0
    team_id: Optional[int] = None
    team_name: Optional[str] = None


class TeamLeaderboardEntry(BaseModel):
    team_id: int
    team_name: str
    team_steps: int
    team_points: Optional[int] = 0


class ChallengeLeaderboardEntry(BaseModel):
    user_id: int
    username: str
    challenge_id: str
    points_awarded: int
    completed_at: Optional[datetime]


