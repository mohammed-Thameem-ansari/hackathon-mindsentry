from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
from typing import List

from ..database import get_db
from . import crud, schemas, models as gam_models
from .. import models as core_models
from datetime import datetime, timedelta


router = APIRouter(prefix="/gamification", tags=["gamification"])


@router.on_event("startup")
def seed_catalog():
    # Phase 2 uses core Challenge model (int id). Skip seeding JSON catalog.
    try:
        _ = next(get_db())
    except Exception:
        pass


@router.post("/assign", response_model=schemas.AssignResponse)
def assign_challenge(payload: schemas.AssignRequest, db: Session = Depends(get_db)):
    score = payload.score
    # Fallback simple rule mapping using core Challenge.type
    if score < 30:
        ctype = "mood-game"
    elif score < 70:
        ctype = "fitness"
    else:
        ctype = "yoga"
    ch = db.query(core_models.Challenge).filter(core_models.Challenge.type == ctype).first()
    if not ch:
        raise HTTPException(400, "No suitable challenge found; seed core challenges first")
    assigned = {
        "id": ch.id,
        "title": ch.title,
        "description": ch.description,
        "base_points": ch.points,
        "tags": [ctype],
        "duration_minutes": None,
        "is_team_challenge": False,
    }
    return {
        "user_id": payload.user_id,
        "assigned": assigned,
        "rationale": "Rule-based assignment",
        "next_check": "in_4_hours",
    }


@router.post("/complete")
def complete_challenge(payload: schemas.CompleteRequest, db: Session = Depends(get_db)):
    challenge = db.query(core_models.Challenge).filter(core_models.Challenge.id == payload.challenge_id).first()
    if not challenge:
        raise HTTPException(404, "Challenge not found")
    # anti-cheat: dedupe recent completion
    recent = db.query(core_models.ChallengeParticipation).filter(
        core_models.ChallengeParticipation.user_id == payload.user_id,
        core_models.ChallengeParticipation.challenge_id == payload.challenge_id,
        getattr(core_models.ChallengeParticipation, "timestamp", getattr(core_models.ChallengeParticipation, "created_at", datetime.utcnow())) >= datetime.utcnow() - timedelta(minutes=30),
    ).first()
    if recent:
        raise HTTPException(400, "Challenge already completed recently")
    # evidence requirement
    if getattr(challenge, "is_evidence_required", False) and not payload.evidence:
        raise HTTPException(400, "Evidence required for this challenge")
    points = challenge.points
    participation = core_models.ChallengeParticipation(
        challenge_id=challenge.id,
        user_id=payload.user_id,
        status="completed",
        score=points,
    )
    db.add(participation)
    ledger = gam_models.PointsLedger(user_id=payload.user_id, source="challenge", points=points)
    db.add(ledger)
    db.commit()
    return {"ok": True, "points_awarded": points}


