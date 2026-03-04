# Voice Scheduling Agent

A real-time voice assistant that helps you schedule Google Calendar events using a mock/local Realtime provider (no paid API required).

## Quick Start

1. **No external API required (mock provider)**

2. **Configure** (optional)
   ```powershell
   notepad .env
   ```
   The default setup uses a mock/local provider for testing. If you later
   integrate a real API, add `PROVIDER_API_KEY=your_token` to `.env`.

3. **Run**
   ```powershell
   .\run.bat
   ```

4. **Open Browser**
   ```
   http://localhost:8000
   ```

5. **Speak**
   "Hi, my name is John. Schedule a meeting tomorrow at 2 PM"

## Requirements

- Python 3.11+
- No external API key required (mock provider)
- Modern web browser

## Project Structure

```
voice_agent/
├── backend/
│   ├── main.py              (FastAPI server)
│   ├── calendar_service.py  (Google Calendar)
│   └── requirements.txt     (Dependencies)
├── frontend/
│   └── index.html           (Web UI)
├── .env                     (Your secrets)
└── run.bat                  (Start server)
```

## Cost

- ~$0.05 per conversation
- ~$1-3 per month for casual use

## Deployment

To deploy to Render.com:
1. Push to GitHub
2. Create Web Service on Render
3. (Optional) Add `PROVIDER_API_KEY` environment variable if using an external provider
4. Deploy

Your app will be live at: `https://your-app.onrender.com`

## License

MIT
