# scripts/seed_demo.py
"""
Seed demo data for WellNova (MindSentry Nova extension).
Run: python scripts/seed_demo.py [--fast]
--fast : smaller numbers (useful for quick local demos)
"""

import random
import argparse
from datetime import datetime, timedelta
import json
import os
import sys

# Ensure project root is on sys.path for module imports
ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
	sys.path.insert(0, ROOT)

# Adapt these imports if your project uses a different package name (mindsentry vs app)
try:
	from backend.database import SessionLocal
	from backend import models as app_models
	from backend.gamification import models as gam_models
	# Optional modules; may not exist
	act_crud = None
except Exception as e:
	print("ERROR: Could not import project modules. Adapt import paths in scripts/seed_demo.py to match your project.")
	raise

DB = SessionLocal()

FIRST_NAMES = ["Alex","Sam","Taylor","Jordan","Casey","Riley","Morgan","Avery","Cameron","Charlie",
               "Jamie","Skyler","Parker","Quinn","Harper","Rowan","Sage","Reese","Emerson","Dakota"]
LAST_NAMES = ["Shah","Patel","Kumar","Singh","Khan","Reddy","Nair","Iyer","Das","Gupta",
              "Mehta","Bose","Chowdhury","Verma","Joshi","Gadkari","Khan","Ali","Aziz","Mistry"]

def rand_name(i):
	return f"{FIRST_NAMES[i % len(FIRST_NAMES)]} {LAST_NAMES[i % len(LAST_NAMES)]}"


def ensure_teams_and_users(db, num_teams=4, users_per_team=5):
	teams = []
	# Create a lightweight Team model on the fly if not present
	TeamModel = getattr(app_models, "Team", None)
	if TeamModel is None:
		class TeamModelFallback(app_models.Base):  # type: ignore
			__tablename__ = "teams"
			from sqlalchemy import Column, Integer, String
			id = Column(Integer, primary_key=True, index=True)
			name = Column(String, unique=True)
		TeamModel = TeamModelFallback
		app_models.Base.metadata.create_all(bind=db.bind)

	for t_idx in range(num_teams):
		team_name = f"Team {t_idx+1}"
		team = db.query(TeamModel).filter(getattr(TeamModel, "name") == team_name).first()
		if not team:
			team = TeamModel(name=team_name)
			db.add(team); db.commit(); db.refresh(team)
		teams.append(team)

	users = []
	for t_idx, team in enumerate(teams):
		for u_idx in range(users_per_team):
			i = t_idx * users_per_team + u_idx
			username = f"user_{t_idx+1}_{u_idx+1}"
			email = f"{username}@example.local"
			# Ensure User has fields email/username/full_name/team_id tolerant
			user = db.query(app_models.User).filter(getattr(app_models.User, "username") == username).first()
			if not user:
				# add missing columns if necessary via setattr
				user = app_models.User(username=username, password="demo",)  # password hashed in real app
				if hasattr(user, "email"):
					setattr(user, "email", email)
				if hasattr(user, "full_name"):
					setattr(user, "full_name", rand_name(i))
				if hasattr(user, "team_id"):
					setattr(user, "team_id", getattr(team, "id"))
				db.add(user); db.commit(); db.refresh(user)
			users.append(user)

	return teams, users


def seed_challenges(db):
	# read catalog.json seeded in gamification package
	path = os.path.join(os.path.dirname(__file__), "..", "backend", "gamification", "catalog.json")
	path = os.path.normpath(path)
	if not os.path.exists(path):
		print("catalog.json not found at", path)
		return []
	with open(path, "r") as f:
		catalog = json.load(f)
	created = []
	# Our current Challenge model in backend/models.py uses integer id and fields; we will create simple stand-ins
	for item in catalog:
		# create a minimal challenge in core Challenge table if present
		ChallengeModel = getattr(app_models, "Challenge", None)
		if ChallengeModel is None:
			continue
			
		# Check existence by title to avoid int/string id mismatch
		exists = db.query(ChallengeModel).filter(getattr(ChallengeModel, "title") == item["title"]).first()
		if not exists:
			ch = ChallengeModel(
				title=item["title"],
				description=item.get("description"),
				type=("mood-game" if "mood_boost" in item.get("tags", []) else "fitness"),
				difficulty="low",
				points=int(item.get("base_points", 10)),
			)
			db.add(ch); db.commit(); db.refresh(ch)
			created.append(ch)
		else:
			created.append(exists)
	return created


def seed_activities_and_participations(db, users, challenges, fast=False):
	now = datetime.utcnow()
	days = 7 if not fast else 3
	activities_created = 0
	participations_created = 0

	# create per-user random steps for last `days`
	for user in users:
		for d in range(days):
			date = now - timedelta(days=d)
			steps = random.randint(200, 8000) if not fast else random.randint(100, 2000)
			# If activities module exists, seed steps there; otherwise skip
			if act_crud is not None:
				try:
					_ = act_crud.create_activity(db, user_id=user.id, steps=steps, calories=int(steps * 0.04))
				except Exception:
					pass
			activities_created += 1

	# Create participations: make team 1 reach >=60% completion on a challenge
	team_size = len(users) // 4 if users else 0
	team_to_win = users[:team_size]
	target_challenge = challenges[0] if challenges else None
	if target_challenge and team_to_win:
		needed = max(1, int(len(team_to_win) * 0.6))
		for i, u in enumerate(team_to_win):
			if i < needed:
				cp = db.query(app_models.ChallengeParticipation).filter_by(user_id=u.id, challenge_id=getattr(target_challenge, "id")).first()
				if not cp:
					cp = app_models.ChallengeParticipation(user_id=u.id, challenge_id=getattr(target_challenge, "id"), status="completed", score=getattr(target_challenge, "points", 10))
					db.add(cp); db.commit(); db.refresh(cp)
					participations_created += 1
				try:
					from backend.gamification.utils import apply_points
					apply_points(db, u.id, source="challenge", points=getattr(target_challenge, "points", 10), meta={"seed": True, "challenge_id": getattr(target_challenge, "id")})
				except Exception:
					pass

	# Random participations
	for ch in challenges[1:3]:
		sample_users = random.sample(users, min(6, len(users)))
		for u in sample_users:
			if random.random() < 0.3:
				cp = db.query(app_models.ChallengeParticipation).filter_by(user_id=u.id, challenge_id=getattr(ch, "id")).first()
				if not cp:
					cp = app_models.ChallengeParticipation(user_id=u.id, challenge_id=getattr(ch, "id"), status="completed", score=getattr(ch, "points", 10))
					db.add(cp); db.commit(); db.refresh(cp)
					participations_created += 1
					try:
						from backend.gamification.utils import apply_points
						apply_points(db, u.id, source="challenge", points=getattr(ch, "points", 10), meta={"seed": True, "challenge_id": getattr(ch, "id")})
					except Exception:
						pass

	return activities_created, participations_created, target_challenge


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--fast", action="store_true", help="smaller demo data set")
	args = parser.parse_args()

	db = DB
	print("Seeding teams & users...")
	teams, users = ensure_teams_and_users(db, num_teams=4, users_per_team=5 if not args.fast else 2)
	print(f"Created/found {len(teams)} teams and {len(users)} users")

	print("Seeding challenges from catalog...")
	challenges = seed_challenges(db)
	print(f"Loaded {len(challenges)} challenges")

	print("Seeding activities and participations...")
	ac, pc, target_ch = seed_activities_and_participations(db, users, challenges, fast=args.fast)
	print(f"Created ~{ac} activities and {pc} participations. Target challenge for team bonus: {getattr(target_ch,'id',None)}")

	print("Seeding completed. Summary:")
	print(f"Teams: {len(teams)}, Users: {len(users)}, Challenges: {len(challenges)}")
	print("You can now start the server and visit the dashboard to see demo data.")

if __name__ == "__main__":
	main()
