from sqlalchemy.orm import Session
from . import models
import json


def get_challenge(db: Session, challenge_id: str):
    return db.query(models.Challenge).filter(models.Challenge.id == challenge_id).first()


def seed_catalog_if_missing(db: Session, catalog_path: str):
    if db.query(models.Challenge).count() == 0:
        with open(catalog_path, "r") as f:
            items = json.load(f)
        for item in items:
            c = models.Challenge(**item)
            db.add(c)
        db.commit()


