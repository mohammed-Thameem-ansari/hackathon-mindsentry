from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from typing import Dict, Any
import asyncio

from ..database import get_db
from . import utils


router = APIRouter(prefix="/team-challenges", tags=["team-challenges"])


@router.post("/evaluate_bonus")
def evaluate_team_bonus(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    challenge_id = payload.get("challenge_id")
    team_id = payload.get("team_id")
    if challenge_id is None or team_id is None:
        raise HTTPException(400, "challenge_id and team_id required")
    res = utils.check_and_apply_team_bonus(db, int(challenge_id), int(team_id), threshold_percent=60.0, per_user_bonus=10)
    # optional broadcast (adapt to your WS manager if available)
    try:
        from ..websocket.manager import manager as ws_manager
        if res["unlocked"]:
            asyncio.create_task(ws_manager.broadcast({"type": "team.bonus_unlocked", "challenge_id": int(challenge_id), "team_id": int(team_id), "percent": res["percent"], "awarded": res["awarded"]}))
            asyncio.create_task(ws_manager.broadcast({"type": "leaderboard.updated"}))
    except Exception:
        pass
    return {"ok": True, "result": res}


@router.post("/complete_and_evaluate/{participation_id}")
def complete_and_evaluate(participation_id: int, db: Session = Depends(get_db)):
    from ..gamification import models as gam_models
    participation = db.query(gam_models.ChallengeParticipation).filter_by(id=participation_id).first()
    if not participation:
        raise HTTPException(404, "Participation not found")
    participation.status = "completed"
    db.commit()
    # award base points using gamification utils
    from ..gamification.utils import apply_points, increment_streak
    ch = db.query(gam_models.Challenge).filter_by(id=participation.challenge_id).first()
    if ch:
        apply_points(db, participation.user_id, source="challenge", points=getattr(ch, "points", 10), meta={"challenge_id": ch.id})
    increment_streak(db, participation.user_id)
    # find team_id if present
    team_id = None
    try:
        # If your User has team_id, pull it
        from ..models import User
        user = db.query(User).filter(User.id == participation.user_id).first()
        team_id = getattr(user, "team_id", None)
    except Exception:
        team_id = None
    res = None
    if team_id:
        res = utils.check_and_apply_team_bonus(db, participation.challenge_id, int(team_id), threshold_percent=60.0, per_user_bonus=10)
        try:
            from ..websocket.manager import manager as ws_manager
            if res["unlocked"]:
                asyncio.create_task(ws_manager.broadcast({"type": "team.bonus_unlocked", "challenge_id": participation.challenge_id, "team_id": int(team_id), "percent": res["percent"], "awarded": res["awarded"]}))
                asyncio.create_task(ws_manager.broadcast({"type": "leaderboard.updated"}))
        except Exception:
            pass
    # broadcast challenge completed
    try:
        from ..websocket.manager import manager as ws_manager
        asyncio.create_task(ws_manager.broadcast({"type": "challenge.completed", "challenge_id": participation.challenge_id, "user_id": participation.user_id}))
    except Exception:
        pass
    return {"ok": True, "team_bonus": res}


@router.get("/percent")
def get_percent(challenge_id: int = Query(...), team_id: int = Query(...), db: Session = Depends(get_db)):
    from .crud import team_completion_percent
    percent, completed_count = team_completion_percent(db, challenge_id, team_id)
    return {"percent": percent, "completed_count": completed_count}


@router.get("/events")
def list_team_bonus_events(db: Session = Depends(get_db)):
    from ..models import TeamBonusEvent
    events = db.query(TeamBonusEvent).order_by(TeamBonusEvent.awarded_at.desc()).all()
    return [
        {
            "id": e.id,
            "team_id": e.team_id,
            "challenge_id": e.challenge_id,
            "percent": e.percent,
            "awarded_at": e.awarded_at.isoformat() if e.awarded_at else None,
        }
        for e in events
    ]


