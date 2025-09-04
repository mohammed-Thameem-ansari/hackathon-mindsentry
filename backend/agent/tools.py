from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Local project imports (adapted)
from ..gamification import models as gam_models


def get_recent_activity(db: Session, user_id: int, days: int = 7) -> Dict[str, Any]:
    now = datetime.utcnow()
    since = now - timedelta(days=days)
    rows = db.query(gam_models.PointsLedger).filter(
        gam_models.PointsLedger.user_id == user_id,
        gam_models.PointsLedger.created_at >= since,
    ).all()
    # Prefer activities if available
    user_total = 0
    try:
        from ..activities import models as activity_models
        q = db.query(activity_models.Activity).filter(
            activity_models.Activity.user_id == user_id,
            activity_models.Activity.recorded_at >= since,
        )
        user_total = sum(a.steps or 0 for a in q.all())
    except Exception:
        user_total = sum([(r.points if str(r.source) == "PointsSource.steps" or r.source == "steps" else 0) for r in rows])
    avg = int(user_total / max(1, days))
    last_7 = [0 for _ in range(days)]
    return {"total_steps": int(user_total), "avg_per_day": avg, "days_active": 0, "last_7": last_7, "since": since.isoformat()}


def get_team_gap(db: Session, user_id: int) -> Dict[str, Any]:
    team_id = None
    try:
        from ..models import User
        u = db.query(User).filter(User.id == user_id).first()
        team_id = getattr(u, "team_id", None)
    except Exception:
        team_id = None
    if team_id is None:
        return {"team_id": None, "team_steps": 0, "top_other_steps": 0, "gap": 0}
    try:
        from ..leaderboard import crud as lb_crud
        rows = lb_crud.team_leaderboard(db, window="week")
        team_steps_map = {getattr(r, "team_id", None): getattr(r, "team_steps", 0) for r in rows}
        team_steps = int(team_steps_map.get(team_id, 0))
        top_other = max([v for k, v in team_steps_map.items() if k != team_id], default=0)
        gap = team_steps - top_other
        return {"team_id": team_id, "team_steps": team_steps, "top_other_steps": int(top_other), "gap": int(gap)}
    except Exception:
        return {"team_id": team_id, "team_steps": 0, "top_other_steps": 0, "gap": 0}


def get_last_assigned(db: Session, user_id: int, limit: int = 5):
    try:
        rows = db.query(gam_models.ChallengeParticipation).filter(
            gam_models.ChallengeParticipation.user_id == user_id
        ).order_by(getattr(gam_models.ChallengeParticipation, "timestamp", getattr(gam_models.ChallengeParticipation, "created_at", None)).desc()).limit(limit).all()
        return [{"challenge_id": r.challenge_id, "status": r.status} for r in rows]
    except Exception:
        return []


def gather_context(db: Session, user_id: int):
    return {
        "recent_activity": get_recent_activity(db, user_id),
        "team_gap": get_team_gap(db, user_id),
        "last_assigned": get_last_assigned(db, user_id),
    }


