from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from . import crud, schemas

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("/individual", response_model=List[schemas.LeaderboardEntry])
def api_individual_leaderboard(window: str = Query("today"), limit: int = Query(50), db: Session = Depends(get_db)):
    # We don't have a user CRUD; return anonymous usernames (user_<id>)
    rows = crud.individual_leaderboard_with_userinfo(db, window, limit, user_crud_get=None)
    return rows


@router.get("/team", response_model=List[schemas.TeamLeaderboardEntry])
def api_team_leaderboard(window: str = Query("today"), limit: int = Query(50), db: Session = Depends(get_db)):
    rows = crud.team_leaderboard(db, window, limit)
    out = []
    for r in rows:
        team_id = getattr(r, "team_id", None)
        team_name = f"Team {team_id}" if team_id is not None else "Unknown Team"
        out.append({
            "team_id": team_id or 0,
            "team_name": team_name,
            "team_steps": int(getattr(r, "team_steps", 0) or 0),
            "team_points": int(getattr(r, "team_points", 0) or 0),
        })
    return out


@router.get("/challenge/{challenge_id}", response_model=List[schemas.ChallengeLeaderboardEntry])
def api_challenge_leaderboard(challenge_id: int, window: str = Query("today"), limit: int = Query(50), db: Session = Depends(get_db)):
    rows = crud.challenge_leaderboard(db, challenge_id, window, limit)
    out = []
    for r in rows:
        username = f"user_{r.user_id}"
        out.append({
            "user_id": r.user_id,
            "username": username,
            "challenge_id": str(challenge_id),
            "points_awarded": int(getattr(r, "points_awarded", 0) or 0),
            "completed_at": getattr(r, "created_at", None),
        })
    return out


