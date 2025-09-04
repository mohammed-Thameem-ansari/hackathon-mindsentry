from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
from typing import List

from ..database import get_db
from . import crud, schemas, models


router = APIRouter(prefix="/gamification", tags=["gamification"])


@router.on_event("startup")
def seed_catalog():
    p = Path(__file__).parent / "catalog.json"
    try:
        db = next(get_db())
        crud.seed_catalog_if_missing(db, str(p))
    except Exception:
        pass


@router.post("/assign", response_model=schemas.AssignResponse)
def assign_challenge(payload: schemas.AssignRequest, db: Session = Depends(get_db)):
    score = payload.score
    catalog = [c.__dict__ for c in db.query(models.Challenge).all()]
    if not catalog:
        raise HTTPException(400, "Challenge catalog is empty")
    assigned = catalog[0]
    if score < 30:
        for c in catalog:
            if "mood_boost" in (c.get("tags") or []):
                assigned = c
                break
    elif score < 70:
        assigned = catalog[0]
    else:
        for c in catalog:
            if "mobility" in (c.get("tags") or []) or str(c.get("id", "")).startswith("yoga"):
                assigned = c
                break
    resp = {
        "user_id": payload.user_id,
        "assigned": assigned,
        "rationale": "Rule-based assignment",
        "next_check": "in_4_hours",
    }
    return resp


@router.post("/complete")
def complete_challenge(payload: schemas.CompleteRequest, db: Session = Depends(get_db)):
    challenge = db.query(models.Challenge).filter(models.Challenge.id == payload.challenge_id).first()
    if not challenge:
        raise HTTPException(404, "Challenge not found")
    points = challenge.base_points
    participation = models.ChallengeParticipation(
        challenge_id=challenge.id,
        user_id=payload.user_id,
        status="completed",
        points_awarded=points,
        evidence=payload.evidence,
    )
    db.add(participation)
    ledger = models.PointsLedger(user_id=payload.user_id, source="challenge", points=points)
    db.add(ledger)
    db.commit()
    return {"ok": True, "points_awarded": points}


