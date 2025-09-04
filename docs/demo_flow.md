# WellNova Hackathon Demo Flow 🚀

## 1. Intro
- Problem: Corporate wellness is boring + low engagement.
- Solution: WellNova (AI-powered, gamified wellness).

## 2. Show Core Features
1. **Leaderboard**
   - Go to `/dashboard` → show team comparison bar chart + challenge breakdown pie chart.
   - Show badges beside usernames.
   - Mention points ledger + streak system in backend.

2. **Wearables Mock**
   - Run:
     ```bash
     curl -X POST http://localhost:8000/api/wearables/mock \
       -H "Content-Type: application/json" \
       -d '{"user_id":1,"steps":1500}'
     ```
   - Refresh leaderboard → watch live update.

3. **Challenges & AI Agent**
   - Assign challenge: `/api/challenges/assign?user_id=1&score=low`
   - Show agent suggesting a yoga challenge → completes → updates leaderboard.
   - Agent also nudges user via WebSocket chat (`agent.nudge`).

4. **Team Bonus**
   - Use `/team-challenges/complete_and_evaluate/{id}` to mark completions.
   - When 60% threshold hit → confetti & toast appear, bonus logged in admin events.

5. **Admin Tools**
   - Upload HR CSV in `/admin/hr-upload`.
   - Show new team/users auto-created.
   - View `/api/team-challenges/events` for audit trail.

6. **Dashboards**
   - Show `/dashboard` → analytics charts (points, team comparison, challenge breakdown).
   - Talk about insights for HR.

## 3. Advanced Features
- Anti-cheat rules (daily cap, dedupe, evidence requirement).
- Agentic AI fallback (works offline).
- Metrics endpoint `/api/monitoring/metrics`.

## 4. Closing
- Future roadmap: real Fitbit API, Slack integration, ML-driven personalization.
- Final WOW: refresh leaderboard → confetti.
