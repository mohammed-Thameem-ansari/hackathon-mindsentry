from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from ..database import get_db
from .. import models as app_models


router = APIRouter(prefix="/monitoring", tags=["monitoring"])


def today_midnight():
    now = datetime.utcnow()
    return datetime(now.year, now.month, now.day)


@router.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    total_users = db.query(app_models.User).count()
    steps_today = 0
    try:
        from ..activities import models as activity_models
        steps_today = (
            db.query(func.coalesce(func.sum(activity_models.Activity.steps), 0))
            .filter(activity_models.Activity.recorded_at >= today_midnight())
            .scalar()
            or 0
        )
    except Exception:
        steps_today = 0
    try:
        active_challenges = db.query(app_models.Challenge).count()
    except Exception:
        active_challenges = 0
    return {"users": int(total_users), "steps_today": int(steps_today), "active_challenges": int(active_challenges)}


