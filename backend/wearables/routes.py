from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session

from ..database import get_db


router = APIRouter(prefix="/wearables", tags=["wearables"])


@router.post("/mock")
def mock_wearables(payload: dict = Body(...), db: Session = Depends(get_db)):
    """
    Accepts either single object:
      { "user_id": 1, "steps": 1200, "timestamp": "2025-09-04T10:00:00Z" }
    Or batch: { "batch": [ {...}, {...} ] }
    For each entry create an activity and award step points.
    """
    entries = payload.get("batch") or [payload]
    results = []
    for e in entries:
        user_id = e.get("user_id")
        steps = int(e.get("steps", 0) or 0)
        calories = e.get("calories")
        # create activity (best-effort)
        try:
            from ..activities import crud as act_crud
            act = act_crud.create_activity(db=db, user_id=user_id, steps=steps, calories=calories)
            activity_id = getattr(act, "id", None)
        except Exception:
            activity_id = None
        # award points via gamification apply
        try:
            from ..gamification.crud import create_points_entry
            res = create_points_entry(db, user_id=user_id, source="steps", points=max(1, steps // 100), meta={"source": "wearables_mock"})
        except Exception:
            res = {"applied": 0}
        results.append({"user_id": user_id, "activity_id": activity_id, "points_applied": res})
    return {"ok": True, "count": len(results), "results": results}


