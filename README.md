## AI Calendar Assistant

A small voice-based web app that helps you **schedule Google Calendar meetings using your voice**.

You speak to the assistant in the browser, it asks for:
- **Your name**
- **Meeting date & time**
- **Meeting title**

Then it creates an event in your **Google Calendar** and shows you a **clickable link** to the event.

---

## 1. Project structure

- **backend/**
  - `main.py` – FastAPI app, Google OAuth, conversation flow, and `/chat` endpoint
  - `calendar_service.py` – creates events in Google Calendar
  - `llm_service.py` – (optional) LLM helpers if you want to use OpenAI / other models
  - `requirments.txt` – Python dependencies
- **frontend/**
  - `index.html` – single-page UI
  - `app.js` – browser speech recognition + calls to `/chat`
- **.env** – environment variables (OpenAI + Google OAuth credentials)

---

## 2. Requirements

- Python 3.9+ (recommended)
- A **Google Cloud** project with:
  - OAuth 2.0 Client ID (`GOOGLE_CLIENT_ID`)
  - Client Secret (`GOOGLE_CLIENT_SECRET`)
  - Authorized redirect URI: `http://localhost:8000/auth/callback`
- (Optional) **OpenAI API key** if you use `llm_service.py`
- A modern browser that supports the Web Speech API (Chrome recommended)

---

## 3. Setup

### 3.1. Create and fill `.env`

In `AI_Calendar_Assisstant/.env`:

```env
OPENAI_API_KEY=your-openai-key-here           # optional for LLM features
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
```

> Do **not** commit real keys to git or share them publicly.

### 3.2. Create & activate a virtual environment (Windows PowerShell)

```bash
cd AI_Calendar_Assisstant
python -m venv .venv
.venv\Scripts\activate
```

### 3.3. Install dependencies

```bash
cd backend
pip install -r requirments.txt
```

---

## 4. Run the app

From the `backend` folder (with the venv activated):

```bash
uvicorn main:app --reload
```

You should see something like:

- `Uvicorn running on http://127.0.0.1:8000`
- `Application startup complete.`

Then open your browser at:

```text
http://localhost:8000
```

---

## 5. How to use

1. **Login with Google**
   - Click **“Login with Google”**.
   - Approve the Calendar permission when prompted.

2. **Start the conversation**
   - Click **“Start Talking”**.
   - The assistant will ask:  
     “Hello! What’s your name so I can schedule a meeting for you?”

3. **Provide details by voice**
   - Say your name (you can say phrases like “Hey, my name is Amy” – it will extract `Amy`).
   - Then say the **date and time** (“next Monday at 3 PM”, “tomorrow at 9 in the morning”, etc.).
   - Then say the **meeting title** (“Project sync with Ali”).

4. **Confirm and create event**
   - The assistant will repeat the details and ask you to **say “yes” to confirm**.
   - If you confirm, it creates the event in Google Calendar.
   - The response includes a **`calendar_link`** and the UI shows:
     - A **Google Calendar link box**
     - **Open** button (opens the event in a new tab)
     - **Copy** button (copies the link to clipboard)

---

## 6. Conversation flow (backend)

The `/chat` endpoint in `backend/main.py` keeps a simple in-memory state per `user_id`:

1. `ask_name` – ask and parse the user’s name from phrases like “my name is Amy”.
2. `ask_datetime` – parse date & time using `dateparser`.
3. `ask_title` – store a free-form meeting title.
4. `confirm` – ask for confirmation and then call `create_calendar_event(...)`.

On success, it returns:

```json
{
  "response": "Meeting created successfully! Here is the Google Calendar link.",
  "calendar_link": "<google_event_url>"
}
```

The frontend (`app.js`) uses this to update the speech output and the calendar link box.

---

## 7. Troubleshooting

- **Nothing happens when I click “Start Talking”**  
  - Make sure your browser **microphone permissions** are allowed.
  - Use Chrome or another browser with Web Speech API support.

- **“Please login with Google first.”**  
  - You must finish the Google OAuth flow so that a `session_id` is stored.

- **Event is not created / Google API error**  
  - Check the server logs for the exact error.
  - Verify the Google credentials in `.env`.
  - Ensure the redirect URI in Google Cloud Console matches `GOOGLE_REDIRECT_URI`.

- **Author✍️ : Osama AT
