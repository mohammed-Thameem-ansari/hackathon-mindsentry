"""
End-to-end backend test script for WellNova (MindSentry Nova).
Run after starting backend with:
    uvicorn backend.main:app --reload --port 8000
Then:
    python scripts/test_endpoints.py
"""

import requests, json, sys

BASE = "http://localhost:8000/api"


def pretty(resp):
    try:
        return json.dumps(resp.json(), indent=2)
    except Exception:
        return resp.text


def test_seed_check():
    print("\n🔹 Checking leaderboard (after seed)...")
    r = requests.get(f"{BASE}/leaderboard/individual")
    print(pretty(r))


def test_user_analytics():
    print("\n🔹 User analytics for user_id=1")
    r = requests.get(f"{BASE}/analytics/user/1")
    print(pretty(r))


def test_wearables():
    print("\n🔹 Posting wearable steps for user_id=1")
    payload = {"user_id": 1, "steps": 2000}
    r = requests.post(f"{BASE}/wearables/mock", json=payload)
    print(pretty(r))


def test_agent_recommendation():
    print("\n🔹 AI Agent Recommendation for user_id=1")
    payload = {"user_id": 1}
    r = requests.post(f"{BASE}/agent/recommendation", json=payload)
    print(pretty(r))


def test_challenge_flow():
    print("\n🔹 Assigning challenge for user_id=1")
    # Our API: POST /challenges/assign/{user_id}?score=INT returns participation_id
    r = requests.post(f"{BASE}/challenges/assign/1", params={"score": 45})
    print(pretty(r))
    try:
        participation_id = r.json().get("participation_id")
    except Exception:
        participation_id = None
    if participation_id:
        print(f"🔹 Completing via team complete_and_evaluate/{participation_id}")
        r2 = requests.post(f"{BASE}/team-challenges/complete_and_evaluate/{participation_id}")
        print(pretty(r2))
    else:
        print("(No participation_id returned; skipping completion)")


def test_team_bonus():
    print("\n🔹 Triggering team bonus evaluation (using participation_id=1 as example)")
    r = requests.post(f"{BASE}/team-challenges/complete_and_evaluate/1")
    print(pretty(r))

    print("\n🔹 Listing team bonus events (admin)")
    # Our current implementation does not require header; if protected, adapt accordingly
    r2 = requests.get(f"{BASE}/team-challenges/events")
    print(pretty(r2))


def test_hr_upload():
    print("\n🔹 Uploading HR CSV (sample)...")
    files = {
        "file": (
            "employees.csv",
            "email,username,team_name,role\n"
            "x1@test.com,x1,Team X,employee\n"
            "x2@test.com,x2,Team X,employee\n",
            "text/csv",
        )
    }
    # Our HR endpoint expects admin_token query param
    r = requests.post(f"{BASE}/hr/upload_csv", params={"admin_token": "REPLACE_WITH_SECURE_TOKEN"}, files=files)
    print(pretty(r))


def test_monitoring():
    print("\n🔹 Monitoring metrics")
    r = requests.get(f"{BASE}/monitoring/metrics")
    print(pretty(r))


if __name__ == "__main__":
    print("🚀 Starting end-to-end API tests...\n")
    try:
        test_seed_check()
        test_user_analytics()
        test_wearables()
        test_agent_recommendation()
        test_challenge_flow()
        test_team_bonus()
        test_hr_upload()
        test_monitoring()
    except Exception as e:
        print("❌ ERROR:", e)
        sys.exit(1)
    print("\n✅ All tests executed. Check above output for correctness.")


