import os
import re
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from datetime import timedelta
import dateparser
from calendar_service import create_calendar_event
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json

load_dotenv()

app = FastAPI()

app.mount("/static", StaticFiles(directory="../frontend"), name="static")

@app.get("/")
async def serve_index():
    return FileResponse("../frontend/index.html")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== Session Storage (In-Memory) ======
sessions = {}

# ====== OAuth Config ======
CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

SCOPES = ["https://www.googleapis.com/auth/calendar"]

# =========================================
# 🔐 AUTH LOGIN
# =========================================
@app.get("/auth/login")
async def login():
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=os.getenv("GOOGLE_REDIRECT_URI")
    )

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent"
    )

    sessions[state] = {}
    return RedirectResponse(authorization_url)


# =========================================
# 🔁 AUTH CALLBACK
# =========================================
@app.get("/auth/callback")
async def callback(request: Request):
    state = request.query_params.get("state")
    code = request.query_params.get("code")

    if state not in sessions:
        return JSONResponse({"error": "Invalid session state"})

    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=os.getenv("GOOGLE_REDIRECT_URI")
    )

    flow.fetch_token(code=code)
    credentials = flow.credentials

    sessions[state]["credentials"] = json.loads(credentials.to_json())

    return RedirectResponse(url=f"http://localhost:8000/?session_id={state}")

@app.get("/auth-status")
async def auth_status(request: Request):
    session_id = request.query_params.get("session_id")
    if session_id and session_id in sessions:
        return {"logged_in": True}
    return {"logged_in": False}


# =========================================
# 🎙 CHAT ENDPOINT
# =========================================
conversation_state = {}


def _extract_name_from_text(text: str):
    """
    Extract a likely first name from phrases like:
      - "my name is Amy"
      - "I'm Amy"
      - "i am Amy"
      - "call me Amy"
    If nothing matches, fall back to a single-word name like "Amy".
    """
    if not text:
        return None

    cleaned = text.strip()

    # Common self-introduction patterns
    m = re.search(
        r"\b(?:my name is|i am|i'm|im|this is|call me)\s+([A-Za-z][A-Za-z'\-]{0,30})\b",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        return m.group(1).strip().title()

    # Fallback: pick the last non-stopword alphabetic token
    stopwords = {
        "hey",
        "hi",
        "hello",
        "yo",
        "my",
        "name",
        "is",
        "im",
        "i'm",
        "i",
        "am",
        "this",
        "call",
        "me",
        "please",
    }
    tokens = re.findall(r"[A-Za-z][A-Za-z'\-]{0,30}", cleaned)
    candidates = [t for t in tokens if t.lower() not in stopwords]
    if not candidates:
        return None

    return candidates[-1].strip().title()


@app.post("/chat")
async def chat(data: dict):
    """
    Conversation flow:
    1. Ask for user's name
    2. Ask for meeting date & time
    3. Ask for meeting title
    4. Confirm and create event in Google Calendar
    """
    user_id = data.get("user_id")
    message = (data.get("message") or "").strip()
    session_id = data.get("session_id")

    if session_id not in sessions:
        return {"response": "Please login with Google first."}

    credentials_dict = sessions[session_id]["credentials"]

    # Start a new conversation
    if user_id not in conversation_state:
        conversation_state[user_id] = {"step": "ask_name"}
        return {"response": "Hello! What's your name so I can schedule a meeting for you?"}

    state = conversation_state[user_id]

    # If conversation already finished
    if state.get("step") == "completed":
        return {"response": "Conversation has ended. Please start a new session for another meeting."}

    # STEP 1: Ask for name
    if state["step"] == "ask_name":
        if not message:
            return {"response": "I didn't catch your name. Please tell me your name."}

        name = _extract_name_from_text(message)
        if not name:
            return {"response": "Sorry, I couldn't understand your name. Please say just your name (for example: 'Amy')."}

        state["name"] = name
        state["step"] = "ask_datetime"
        return {
            "response": f"Nice to meet you, {state['name']}! When should I schedule the meeting? Please say the date and time."
        }

    # STEP 2: Ask for date & time
    if state["step"] == "ask_datetime":
        parsed_datetime = dateparser.parse(message)
        if not parsed_datetime:
            return {
                "response": "I couldn't understand the date and time. Please say something like 'next Monday at 3 PM'."
            }

        state["parsed_datetime"] = parsed_datetime
        state["step"] = "ask_title"
        formatted_date = parsed_datetime.strftime("%Y-%m-%d %H:%M")
        return {
            "response": f"Great. What should I call this meeting on {formatted_date}?"
        }

    # STEP 3: Ask for meeting title
    if state["step"] == "ask_title":
        if not message:
            return {"response": "Please tell me a title for the meeting."}

        state["title"] = message
        state["step"] = "confirm"
        formatted_date = state["parsed_datetime"].strftime("%Y-%m-%d %H:%M")
        return {
            "response": f"Please confirm: schedule meeting '{state['title']}' for {state['name']} on {formatted_date}? Say yes to confirm."
        }

    # STEP 4: Confirm and create event
    if state["step"] == "confirm":
        if "yes" in message.lower():
            start_dt = state["parsed_datetime"]
            start_time = start_dt.isoformat()
            end_dt = start_dt + timedelta(hours=1)
            end_time = end_dt.isoformat()

            try:
                link = create_calendar_event(
                    state["title"],
                    start_time,
                    end_time,
                    credentials_dict,
                )
                state["step"] = "completed"
                return {
                    "response": f"Meeting created successfully! Here is the Google Calendar link.",
                    "calendar_link": link,
                }
            except Exception as e:
                state["step"] = "completed"
                return {"response": f"Error creating event: {str(e)}"}

        # Any non-yes answer ends the conversation
        state["step"] = "completed"
        return {"response": "Okay, I won't create the meeting. Start a new session if you want to schedule another one."}
