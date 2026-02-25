from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models as core_models
from ..gamification import models as gam_models


router = APIRouter()


@router.post("/challenges/assign/{user_id}")
def assign_challenge(user_id: int, score: int, db: Session = Depends(get_db)):
    """
    Assigns a challenge to user based on score.
    - Low score → mood-boosting fun challenge
    - High score → wellness / yoga / endurance
    """
    if score < 40:
        challenge_type = "mood-game"
    elif score < 70:
        challenge_type = "fitness"
    else:
        challenge_type = "yoga"

    challenge = db.query(core_models.Challenge).filter(core_models.Challenge.type == challenge_type).first()
    if not challenge:
        return {"msg": f"No {challenge_type} challenge found"}

    participation = core_models.ChallengeParticipation(
        user_id=user_id,
        challenge_id=challenge.id,
        status="assigned",
    )
    db.add(participation)
    db.commit()
    db.refresh(participation)

    return {"msg": "Challenge assigned", "challenge": challenge.title, "participation_id": participation.id}


@router.post("/challenges/complete/{participation_id}")
def complete_challenge(participation_id: int, db: Session = Depends(get_db)):
    participation = db.query(core_models.ChallengeParticipation).filter_by(id=participation_id).first()
    if not participation:
        return {"error": "Participation not found"}

    participation.status = "completed"
    # ensure challenge relationship loaded
    challenge = participation.challenge or db.query(core_models.Challenge).filter(core_models.Challenge.id == participation.challenge_id).first()
    participation.score = challenge.points if challenge else 0

    # update leaderboard (points_ledger) using gamification ledger
    ledger_entry = gam_models.PointsLedger(
        user_id=participation.user_id,
        source=gam_models.PointsSource.challenge,
        points=participation.score,
        meta={"reason": f"Completed {challenge.title}"} if challenge else None,
    )
    db.add(ledger_entry)
    db.commit()

    return {"msg": "Challenge completed", "points_awarded": participation.score}


