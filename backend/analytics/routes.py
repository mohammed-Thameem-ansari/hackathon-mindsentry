from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from . import service


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/user/{user_id}")
def user_analytics(user_id: int, db: Session = Depends(get_db)):
    return service.user_progress(db, user_id)


@router.get("/team")
def team_analytics(db: Session = Depends(get_db)):
    return service.team_comparison(db)


@router.get("/challenges")
def challenge_analytics(db: Session = Depends(get_db)):
    return service.challenge_breakdown(db)


