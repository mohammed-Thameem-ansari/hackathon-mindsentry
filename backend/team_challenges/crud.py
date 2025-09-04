from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
from ..gamification import models as gam_models
from .. import models as app_models
from sqlalchemy import func


def get_participations_for_challenge(db: Session, challenge_id: int, window_days: int = 7):
    since = datetime.utcnow() - timedelta(days=window_days)
    rows = db.query(app_models.ChallengeParticipation).filter(
        app_models.ChallengeParticipation.challenge_id == challenge_id,
        app_models.ChallengeParticipation.timestamp >= since,
    ).all()
    return rows


def _get_team_member_ids(db: Session, team_id: int):
    try:
        from ..users import crud as user_crud  # optional module
        members = user_crud.get_users_by_team(db, team_id)
        return [m.id for m in members]
    except Exception:
        # fallback: query users table directly if team_id column exists
        try:
            members = db.query(app_models.User).filter(getattr(app_models.User, "team_id", None) == team_id).all()
            return [m.id for m in members]
        except Exception:
            return []


def team_completion_percent(db: Session, challenge_id: int, team_id: int, window_days: int = 7):
    member_ids = _get_team_member_ids(db, team_id)
    if not member_ids:
        return 0.0, 0
    participations = db.query(app_models.ChallengeParticipation.user_id).filter(
        app_models.ChallengeParticipation.challenge_id == challenge_id,
        app_models.ChallengeParticipation.user_id.in_(member_ids),
        app_models.ChallengeParticipation.status == "completed",
    ).distinct().all()
    completed_ids = {r.user_id for r in participations}
    completed_count = len(completed_ids)
    percent = (completed_count / len(member_ids)) * 100.0 if member_ids else 0.0
    return percent, completed_count


def record_team_bonus_award(db: Session, team_id: int, challenge_id: int, percent: float):
    from ..models import TeamBonusEvent
    event = TeamBonusEvent(team_id=team_id, challenge_id=challenge_id, percent=percent)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def award_team_bonus_points(db: Session, team_id: int, amount_per_user: int, metadata: dict = None, challenge_id: int | None = None):
    member_ids = _get_team_member_ids(db, team_id)
    awarded = []
    from ..gamification.utils import apply_points
    for uid in member_ids:
        meta = {"team_bonus": True}
        if metadata:
            meta.update(metadata)
        if challenge_id is not None:
            meta["challenge_id"] = challenge_id
        res = apply_points(db, uid, source="bonus", points=amount_per_user, meta=meta)
        awarded.append({"user_id": uid, "applied": res.get("applied", 0)})
    return awarded


