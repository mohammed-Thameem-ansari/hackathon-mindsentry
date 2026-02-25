from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class RecommendationRequest(BaseModel):
    user_id: int


class RecommendationResponse(BaseModel):
    user_id: int
    challenge_id: Optional[str] = None
    challenge_title: Optional[str] = None
    nudge_text: Optional[str] = None
    justification: Optional[str] = None
    confidence: Optional[float] = 0.0
    fallback: Optional[bool] = False


class EvaluateTriggerRequest(BaseModel):
    user_id: Optional[int] = None
    run_all: Optional[bool] = False


