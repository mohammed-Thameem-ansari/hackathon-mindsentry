import asyncio

def send_to_challenge_room(challenge_id: int, message: dict):
    try:
        from ..websocket.manager import manager
        asyncio.create_task(manager.broadcast({"type": "challenge.room", "challenge_id": challenge_id, "payload": message}))
    except Exception:
        pass


