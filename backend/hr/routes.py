from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
import csv, io
from sqlalchemy.orm import Session
from ..database import get_db

router = APIRouter(prefix="/hr", tags=["hr"])


@router.post("/upload_csv")
def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db), admin_token: str | None = None):
    # simple token check
    import os
    expected = os.getenv("ADMIN_TOKEN") or "REPLACE_WITH_SECURE_TOKEN"
    if admin_token != expected:
        raise HTTPException(403, "admin token required")
    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    created = []
    try:
        from ..users import crud as user_crud
    except Exception:
        user_crud = None
    try:
        from ..teams import crud as team_crud
    except Exception:
        team_crud = None

    for row in reader:
        username = row.get("username")
        email = row.get("email")
        team_name = row.get("team_name") or "Unassigned"
        team_id = None
        if team_crud:
            team = team_crud.get_or_create_team(db, team_name)
            team_id = getattr(team, "id", None)
        if user_crud:
            user = user_crud.create_user_from_hr(db, username=username, email=email, team_id=team_id)
            created.append({"user_id": getattr(user, "id", None), "team_id": team_id})
    return {"created": created, "count": len(created)}


