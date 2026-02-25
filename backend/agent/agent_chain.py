import json
from pathlib import Path
from sqlalchemy.orm import Session

from .tools import gather_context


PROMPT_PATH = Path(__file__).parent / "prompt_templates" / "recommend_prompt.txt"


def load_prompt():
    try:
        return PROMPT_PATH.read_text()
    except Exception:
        return ""


def recommend_for_user(db: Session, user_id: int, llm_api_key: str | None = None):
    """
    Returns a dict matching RecommendationResponse schema. Falls back to rule-based if LLM unavailable.
    """
    # gather context
    context = gather_context(db, user_id)
    prompt_text = load_prompt() + "\n\nCONTEXT_JSON:\n" + json.dumps(context)
    try:
        # Lazy import to avoid hard dependency if OPENAI not set
        from langchain import OpenAI, LLMChain
        from langchain.prompts import PromptTemplate as LC_PromptTemplate

        llm = OpenAI(temperature=0.2, openai_api_key=llm_api_key)
        prompt = LC_PromptTemplate(input_variables=["text"], template="{text}")
        chain = LLMChain(llm=llm, prompt=prompt)
        raw = chain.run(prompt_text)
        try:
            parsed = json.loads(raw.strip())
        except Exception:
            import re
            m = re.search(r"(\{.*\})", raw, re.S)
            parsed = json.loads(m.group(1)) if m else None
        if not parsed:
            return rule_based_recommendation(db, user_id)
        resp = {
            "user_id": user_id,
            "challenge_id": parsed.get("challenge_id"),
            "challenge_title": parsed.get("challenge_title"),
            "nudge_text": parsed.get("nudge_text"),
            "justification": parsed.get("justification"),
            "confidence": float(parsed.get("confidence", 0.5)),
            "fallback": False,
        }
        # validate challenge exists (accepts int or string id depending on your table)
        from ..gamification import crud as gam_crud
        ch = None
        if resp["challenge_id"] and resp["challenge_id"] != "none":
            ch = gam_crud.get_challenge_by_id(db, resp["challenge_id"])
        if not ch and resp["challenge_id"] not in (None, "none"):
            return rule_based_recommendation(db, user_id)
        return resp
    except Exception:
        return rule_based_recommendation(db, user_id)


def rule_based_recommendation(db: Session, user_id: int):
    ctx = gather_context(db, user_id)
    total = ctx.get("recent_activity", {}).get("total_steps", 0)
    if total < 1000:
        return {
            "user_id": user_id,
            "challenge_id": "walk_500",
            "challenge_title": "500 Step Break",
            "nudge_text": "Short walk: 500 steps — small wins stack up! 🚶",
            "justification": "Low recent activity; a short walk is easy and mood-boosting.",
            "confidence": 0.4,
            "fallback": True,
        }
    gap = ctx.get("team_gap", {}).get("gap", 0)
    if gap < 0:
        return {
            "user_id": user_id,
            "challenge_id": "walk_500",
            "challenge_title": "500 Step Break",
            "nudge_text": "Your team is behind — 500-step burst to catch up! 💪",
            "justification": "Team is behind top team; quick team challenge can flip leaderboard.",
            "confidence": 0.6,
            "fallback": True,
        }
    return {
        "user_id": user_id,
        "challenge_id": "breath_box",
        "challenge_title": "2-min Box Breathing",
        "nudge_text": "Two-minute box breathing to reset and refresh 🧘",
        "justification": "Default suggestion for balanced users.",
        "confidence": 0.5,
        "fallback": True,
    }


