from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import func

from ..gamification import models as gam_models
from .. import models as app_models


def user_progress(db: Session, user_id: int, days: int = 7):
    since = datetime.utcnow() - timedelta(days=days)
    total_points = (
        db.query(func.coalesce(func.sum(gam_models.PointsLedger.points), 0))
        .filter(
            gam_models.PointsLedger.user_id == user_id,
            gam_models.PointsLedger.created_at >= since,
        )
        .scalar()
        or 0
    )

    # ChallengeParticipation timestamp/created_at compatibility
    ts_col = getattr(gam_models.ChallengeParticipation, "timestamp", getattr(gam_models.ChallengeParticipation, "created_at", None))
    if ts_col is None:
        ts_filter = True
    else:
        ts_filter = ts_col >= since

    completed = (
        db.query(gam_models.ChallengeParticipation)
        .filter(
            gam_models.ChallengeParticipation.user_id == user_id,
            gam_models.ChallengeParticipation.status == "completed",
            ts_filter,
        )
        .count()
    )

    return {
        "user_id": user_id,
        "days": days,
        "total_points": int(total_points),
        "completed_challenges": int(completed),
    }


def team_comparison(db: Session, days: int = 7):
    since = datetime.utcnow() - timedelta(days=days)
    q = (
        db.query(
            app_models.User.team_id,
            func.coalesce(func.sum(gam_models.PointsLedger.points), 0).label("team_points"),
        )
        .join(gam_models.PointsLedger, gam_models.PointsLedger.user_id == app_models.User.id)
        .filter(gam_models.PointsLedger.created_at >= since)
        .group_by(app_models.User.team_id)
        .all()
    )
    return [{"team_id": getattr(r, "team_id", None), "team_points": int(getattr(r, "team_points", 0) or 0)} for r in q]


def challenge_breakdown(db: Session, days: int = 7):
    since = datetime.utcnow() - timedelta(days=days)
    ts_col = getattr(gam_models.ChallengeParticipation, "timestamp", getattr(gam_models.ChallengeParticipation, "created_at", None))
    if ts_col is None:
        ts_filter = True
    else:
        ts_filter = ts_col >= since

    q = (
        db.query(
            gam_models.Challenge.type,
            func.count(gam_models.ChallengeParticipation.id).label("count"),
        )
        .join(
            gam_models.ChallengeParticipation,
            gam_models.Challenge.id == gam_models.ChallengeParticipation.challenge_id,
        )
        .filter(ts_filter, gam_models.ChallengeParticipation.status == "completed")
        .group_by(gam_models.Challenge.type)
        .all()
    )
    return [{"type": getattr(r, "type", "unknown"), "count": int(getattr(r, "count", 0) or 0)} for r in q]


