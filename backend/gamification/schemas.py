from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChallengeBase(BaseModel):
    id: str
    title: str
    description: Optional[str]
    base_points: int
    tags: Optional[List[str]] = []
    duration_minutes: Optional[int] = None
    is_team_challenge: Optional[bool] = False


class ChallengeOut(ChallengeBase):
    created_at: Optional[datetime]


class AssignRequest(BaseModel):
    user_id: int
    score: int
    lookback_days: Optional[int] = 7


class AssignResponse(BaseModel):
    user_id: int
    assigned: ChallengeOut
    rationale: str
    next_check: Optional[str]


class CompleteRequest(BaseModel):
    user_id: int
    challenge_id: str
    evidence: Optional[Dict[str, Any]] = None
    team_id: Optional[int] = None


