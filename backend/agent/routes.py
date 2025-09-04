from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from ..database import get_db
from .schemas import RecommendationRequest, RecommendationResponse, EvaluateTriggerRequest
from .agent_chain import recommend_for_user


router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/recommendation", response_model=RecommendationResponse)
def recommendation(payload: RecommendationRequest, db: Session = Depends(get_db)):
    res = recommend_for_user(db, payload.user_id)
    return res


@router.post("/triggers/evaluate")
def evaluate_triggers(payload: EvaluateTriggerRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if payload.run_all:
        # schedule background tasks per user if user listing exists
        try:
            from ..models import User
            users = db.query(User).all()
            for u in users:
                background_tasks.add_task(_evaluate_and_post, u.id)
            return {"ok": True, "scheduled": len(users)}
        except Exception:
            raise HTTPException(400, "User listing not available")
    elif payload.user_id:
        res = recommend_for_user(db, payload.user_id)
        # optional: broadcast via WS if available
        try:
            from ..websocket.manager import manager as ws_manager
            if res.get("nudge_text"):
                import asyncio
                asyncio.create_task(ws_manager.broadcast({"type": "agent.nudge", "user_id": payload.user_id, "text": res.get("nudge_text"), "challenge_id": res.get("challenge_id")}))
        except Exception:
            pass
        return res
    else:
        raise HTTPException(400, "user_id or run_all required")


def _evaluate_and_post(user_id: int):
    from ..database import SessionLocal
    db = SessionLocal()
    try:
        res = recommend_for_user(db, user_id)
        try:
            from ..websocket.manager import manager as ws_manager
            if res.get("nudge_text"):
                import asyncio
                asyncio.get_event_loop().create_task(ws_manager.broadcast({"type": "agent.nudge", "user_id": user_id, "text": res.get("nudge_text"), "challenge_id": res.get("challenge_id")}))
        except Exception:
            pass
    finally:
        db.close()


