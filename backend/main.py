"""
File: main.py
Purpose: This is the main backend file for the FastAPI application. It defines API endpoints and WebSocket functionality.

Flow:
1. Sentiment Analysis:
   - Endpoint: /analyze
   - Flow: sentiment.py -> main.py

2. Audio Transcription:
   - Endpoint: /transcribe
   - Flow: transcription.py -> main.py

3. WebSocket for Chat Rooms:
   - Endpoint: /ws/{room_id}
   - Flow: main.py (manages WebSocket connections and room participants)

4. HTML Templates:
   - Endpoint: /
   - Endpoint: /therapy
   - Endpoint: /meeting-room
   - Flow: main.py -> templates/*.html
"""

from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException, status, Form, Depends
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import MetaData
from .sentiment import analyze_sentiment
from .transcription import transcribe_audio
from .database import engine, get_db
from .models import Base, User, Text
# from audio_logic import process_audio
from passlib.context import CryptContext
import os
from typing import Dict, List
from random import choice
from .ai_chat import get_ai_response


templates = Jinja2Templates(directory="templates")

app = FastAPI()

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS setup to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Drop and recreate tables (for development only; remove in production)
metadata = MetaData()
metadata.reflect(bind=engine)  # Bind the engine here
metadata.drop_all(bind=engine)  # Drop all tables
Base.metadata.create_all(bind=engine)  # Recreate tables

# OAuth2 for token-based auth (placeholder)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Session management
def get_current_user(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return None
    return {"uid": int(user_id), "logged_in": True}

class TextInput(BaseModel):
    text: str

rooms = {}

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
async def signup(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = pwd_context.hash(password)
    new_user = User(username=username, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user or not pwd_context.verify(password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="user_id", value=str(db_user.id), httponly=True)  # Updated to use id
    return response

@app.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("user_id")
    return response

@app.get("/therapy", response_class=HTMLResponse)
def therapy_page(request: Request):
    return templates.TemplateResponse("therapy.html", {"request": request})

@app.get("/meeting-room", response_class=HTMLResponse)
def meeting_room(request: Request):
    return templates.TemplateResponse("meeting_room.html", {"request": request})

@app.get("/ai-chat", response_class=HTMLResponse)
def ai_chat_page(request: Request):
    """
    Serve the AI chat page.
    """
    return templates.TemplateResponse("ai_chat.html", {"request": request})

@app.get("/voice-chatbot", response_class=HTMLResponse)
def voice_chatbot_page(request: Request):
    """
    Serve the Voice Chatbot page.
    """
    return templates.TemplateResponse("voice_chatbot.html", {"request": request})

@app.post("/api/ai-chat")
async def voice_chat(input: TextInput):
    """
    Handle voice chat messages using the AI chat system.
    """
    try:
        response_data = await get_ai_response(input.text, [])
        return {"response": response_data["response"]}
    except Exception as e:
        print(f"Error in voice chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing voice chat response")

# Post_request to analyze sentiment

@app.post("/analyze")
async def analyze_text(input: TextInput, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not logged in")
    result = analyze_sentiment(input.text)
    text_entry = Text(
        user_id=user["uid"],  # Updated to use user_id
        text=input.text,
        tscore=result["confidence"],
        sentiment=result["sentiment"],
        label="text"
    )
    db.add(text_entry)
    db.commit()
    return result

@app.post("/transcribe")
async def transcribe_audio_endpoint(file: UploadFile = File(...), db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not logged in")
    temp_path = f"temp_audio_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
        transcription = transcribe_audio(temp_path)  # Pass temp_path directly
        if "text" in transcription:
            result = analyze_sentiment(transcription["text"])
            text_entry = Text(
                user_id=user["uid"],  # Fixed typo from uid to user_id
                text=transcription["text"],
                tscore=result["confidence"],
                sentiment=result["sentiment"],
                label="uploaded" if file.filename else "direct_audio"
            )
            db.add(text_entry)
            db.commit()
            return {"transcription": transcription["text"], "sentiment": result}
        return transcription
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# Room: List of connected websockets
connected_clients: Dict[str, List[WebSocket]] = {}

# Add a list of colors for user names
USER_COLORS = ["#FF5733", "#33FF57", "#3357FF", "#FF33A1", "#A133FF", "#33FFF5"]

# Room: Dict of WebSocket -> (nickname, color, message history, ai_chat_mode)
client_nicknames: Dict[str, Dict[WebSocket, tuple]] = {}
# Example: client_nicknames = { "general": { websocket1: ("Ali", "#FF5733", [], False), websocket2: ("Sara", "#33FF57", [], True) } }

async def broadcast_to_room(room_id: str, data: dict):
    for client in connected_clients[room_id]:
        await client.send_json(data)
        
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str = "general"):
    await websocket.accept()

    if room_id not in connected_clients:
        connected_clients[room_id] = []
        client_nicknames[room_id] = {}

    nickname = await websocket.receive_text()
    color = choice(USER_COLORS)
    connected_clients[room_id].append(websocket)
    message_history = []  # Initialize empty history for this user
    ai_chat_mode = False  # Track whether the user is in AI chat mode
    client_nicknames[room_id][websocket] = (nickname, color, message_history, ai_chat_mode)

    # Send a "connected" system message to the user
    await websocket.send_json({
        "type": "system",
        "message": "Connected to the room.",
    })

    # Notify the user if they are alone in the room
    is_alone = len(connected_clients[room_id]) == 1
    if is_alone:
        await websocket.send_json({
            "type": "system",
            "message": "You're alone in the room. Would you like to chat with our AI chatbot?",
            "showAiOption": True
        })

    # Notify others about the new user
    await broadcast_to_room(room_id, {
        "type": "join",
        "nickname": nickname,
        "color": color,
        "isAlone": is_alone
    })

    try:
        while True:
            message = await websocket.receive_text()

            await broadcast_to_room(room_id, {
                "type": "message",
                "nickname": nickname,
                "message": message,
                "color": color,
                "isAI": False
            })
    except WebSocketDisconnect:
        connected_clients[room_id].remove(websocket)
        is_alone = len(connected_clients[room_id]) == 1
        await broadcast_to_room(room_id, {
            "type": "leave",
            "nickname": nickname,
            "color": color,
            "isAlone": is_alone
        })
        del client_nicknames[room_id][websocket]

        if not connected_clients[room_id]:
            del connected_clients[room_id]
            del client_nicknames[room_id]


async def api_ai_chat(input: TextInput):
    """
    Handle AI chat messages.
    """
    try:
        response_data = await get_ai_response(input.text, [])
        return {"response": response_data["response"]}
    except Exception as e:
        print(f"Error in AI chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing AI response")


audio_room_clients = {}
@app.websocket("/ws/audio-room")
async def audio_room_websocket(websocket: WebSocket):
    await websocket.accept()
    username = None
    try:
        while True:
            data = await websocket.receive_json()
            if data["type"] == "join":
                username = data["username"]
                audio_room_clients[username] = websocket
                for client in audio_room_clients.values():
                    await client.send_json({"type": "join", "username": username})
                # Notify if the user is alone in the room
                if len(audio_room_clients) == 1:
                    await websocket.send_json({
                        "type": "system",
                        "message": "You're alone in the room. Would you like to chat with our AI chatbot?",
                        "showAiOption": True
                    })
            elif data["type"] == "leave":
                if username in audio_room_clients:
                    del audio_room_clients[username]
                    for client in audio_room_clients.values():
                        await client.send_json({"type": "leave", "username": username})
            else:
                receiver = data.get("receiver")
                if receiver in audio_room_clients:
                    await audio_room_clients[receiver].send_json(data)
    except WebSocketDisconnect:
        if username in audio_room_clients:
            del audio_room_clients[username]
            for client in audio_room_clients.values():
                await client.send_json({"type": "leave", "username": username})