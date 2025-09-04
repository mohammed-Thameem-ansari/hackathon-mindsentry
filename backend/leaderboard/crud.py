from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import func

# Adapt imports to local project structure
try:
    from ..activities import models as activity_models
except Exception:
    activity_models = None

from ..gamification import models as gam_models


def get_since(window: str):
    now = datetime.utcnow()
    if window == "today":
        return datetime(now.year, now.month, now.day)
    if window == "week":
        return now - timedelta(days=7)
    return now - timedelta(days=1)


def individual_leaderboard(db: Session, window: str = "today", limit: int = 50):
    since = get_since(window)
    if activity_models is None:
        # if no Activity model, fall back to points only
        q = db.query(
            gam_models.PointsLedger.user_id,
            func.literal(0).label("total_steps"),
            func.coalesce(func.sum(gam_models.PointsLedger.points), 0).label("total_points"),
        ).filter(gam_models.PointsLedger.created_at >= since)
        q = q.group_by(gam_models.PointsLedger.user_id).order_by(func.sum(gam_models.PointsLedger.points).desc()).limit(limit)
        return q.all()

    q = db.query(
        activity_models.Activity.user_id,
        func.coalesce(func.sum(activity_models.Activity.steps), 0).label("total_steps"),
        func.coalesce(func.sum(gam_models.PointsLedger.points), 0).label("total_points"),
    ).outerjoin(
        gam_models.PointsLedger, gam_models.PointsLedger.user_id == activity_models.Activity.user_id
    ).filter(activity_models.Activity.recorded_at >= since)
    q = q.group_by(activity_models.Activity.user_id).order_by(func.sum(activity_models.Activity.steps).desc()).limit(limit)
    return q.all()


def individual_leaderboard_with_userinfo(db: Session, window: str = "today", limit: int = 50, user_crud_get=None):
    rows = individual_leaderboard(db, window, limit)
    out = []
    for r in rows:
        user = None
        if user_crud_get:
            try:
                user = user_crud_get(db, r.user_id)
            except Exception:
                user = None
        username = getattr(user, "username", getattr(user, "full_name", f"user_{r.user_id}"))
        team_id = getattr(user, "team_id", None)
        team_name = None
        if team_id:
            try:
                from ..teams import crud as team_crud  # optional
                team = team_crud.get_team(db, team_id)
                team_name = getattr(team, "name", None)
            except Exception:
                team_name = None
        out.append({
            "user_id": r.user_id,
            "username": username,
            "total_steps": int(getattr(r, "total_steps", 0) or 0),
            "total_points": int(getattr(r, "total_points", 0) or 0),
            "team_id": team_id,
            "team_name": team_name,
        })
    return out


def team_leaderboard(db: Session, window: str = "today", limit: int = 50):
    since = get_since(window)
    try:
        from ..models import User as UserModel
    except Exception:
        return []

    if activity_models is None:
        # fallback based on points only
        q = db.query(
            UserModel.team_id,
            func.literal(0).label("team_steps"),
            func.coalesce(func.sum(gam_models.PointsLedger.points), 0).label("team_points"),
        ).join(
            gam_models.PointsLedger, gam_models.PointsLedger.user_id == UserModel.id
        ).filter(gam_models.PointsLedger.created_at >= since)
        q = q.group_by(UserModel.team_id).order_by(func.sum(gam_models.PointsLedger.points).desc()).limit(limit)
        return q.all()

    q = db.query(
        UserModel.team_id,
        func.coalesce(func.sum(activity_models.Activity.steps), 0).label("team_steps"),
        func.coalesce(func.sum(gam_models.PointsLedger.points), 0).label("team_points"),
    ).join(
        activity_models.Activity, activity_models.Activity.user_id == UserModel.id
    ).join(
        gam_models.PointsLedger, gam_models.PointsLedger.user_id == UserModel.id, isouter=True
    ).filter(activity_models.Activity.recorded_at >= since)
    q = q.group_by(UserModel.team_id).order_by(func.sum(activity_models.Activity.steps).desc()).limit(limit)
    return q.all()


def challenge_leaderboard(db: Session, challenge_id: int, window: str = "today", limit: int = 50):
    since = get_since(window)
    # use participation table in core models
    from ..models import ChallengeParticipation
    q = db.query(
        ChallengeParticipation.user_id,
        func.coalesce(func.sum(ChallengeParticipation.score), 0).label("points_awarded"),
        ChallengeParticipation.timestamp.label("created_at"),
    ).filter(ChallengeParticipation.challenge_id == challenge_id)
    q = q.filter(ChallengeParticipation.timestamp >= since)
    q = q.group_by(ChallengeParticipation.user_id, ChallengeParticipation.timestamp)
    q = q.order_by(func.sum(ChallengeParticipation.score).desc()).limit(limit)
    return q.all()


