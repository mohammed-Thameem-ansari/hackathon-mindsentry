from datetime import datetime
from sqlalchemy.orm import Session


def check_and_apply_team_bonus(db: Session, challenge_id: int, team_id: int, threshold_percent: float = 60.0, per_user_bonus: int = 10):
    """
    Check percent completion; if >= threshold_percent, award team bonus points to all members.
    Returns: {unlocked:bool, percent:float, awarded:list}
    """
    from .crud import team_completion_percent, award_team_bonus_points, record_team_bonus_award
    percent, _ = team_completion_percent(db, challenge_id, team_id)
    if percent >= threshold_percent:
        awarded = award_team_bonus_points(db, team_id, per_user_bonus, metadata={"team_bonus": True}, challenge_id=challenge_id)
        record_team_bonus_award(db, team_id, challenge_id, awarded_at=datetime.utcnow())
        return {"unlocked": True, "percent": percent, "awarded": awarded}
    return {"unlocked": False, "percent": percent, "awarded": []}


