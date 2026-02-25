from datetime import datetime, timedelta
from sqlalchemy.orm import Session


def can_call_agent(db: Session, user_id: int, cooldown_min: int = 60) -> bool:
    try:
        from ..agent_models import AgentCallLog
    except Exception:
        # inline model if separate not present
        from sqlalchemy import Column, Integer, DateTime, ForeignKey
        from ..database import Base
        class AgentCallLog(Base):
            __tablename__ = "agent_call_log"
            id = Column(Integer, primary_key=True)
            user_id = Column(Integer, ForeignKey("users.id"))
            created_at = Column(DateTime, default=datetime.utcnow)
    rec = db.execute(
        "SELECT created_at FROM agent_call_log WHERE user_id = :uid ORDER BY created_at DESC LIMIT 1",
        {"uid": user_id},
    ).fetchone()
    if not rec:
        return True
    last = rec[0]
    return (datetime.utcnow() - last) > timedelta(minutes=cooldown_min)


