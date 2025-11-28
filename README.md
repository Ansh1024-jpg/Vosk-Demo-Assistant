# Vosk Demo Assistant

An offline speech-driven assistant powered by Vosk/Kaldi for speech recognition, a FastAPI backend streaming real-time transcripts over WebSocket, and a React + Vite frontend that visualizes state and chat.

- Wake word: say "hey assistant" to start.
- The assistant asks a short series of questions; answer by speaking or typing.
- Runs fully offline using the small English Vosk model.

## Project Structure

```
backend/
  server.py              # FastAPI + WebSocket server, Vosk recognizer, mic loop
  model_downloader.py    # One-shot downloader for the Vosk small English model
  requirements.txt       # Python dependencies
  test_server.py         # (Dev stub) Flask-SocketIO demo, not used by main app
  model/                 # Vosk model directory (created by downloader)
frontend/
  src/, public/          # React app (Vite)
  package.json           # Frontend scripts and deps
```

## Prerequisites

- Python 3.9–3.12 (64-bit recommended)
- Node.js 18+ (LTS recommended)
- A working microphone on the machine running the backend
- Windows note: `pyaudio` may require a prebuilt wheel (see Troubleshooting)

## Quick Start

Open two terminals: one for the backend, one for the frontend.

### 1) Backend (FastAPI + Vosk)

```pwsh
# From repo root
cd backend

# (Optional) Create and activate a virtual environment
python -m venv .venv
. .venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Download the offline Vosk model (one-time)
python model_downloader.py

# Start the server (WebSocket on ws://localhost:5000/ws)
python server.py
```

When the server starts, it loads the Vosk model and begins listening to the local microphone. It broadcasts recognition events to connected WebSocket clients.

### 2) Frontend (React + Vite)

```pwsh
# In a second terminal, from repo root
cd frontend
npm install
npm run dev
```

Open the URL shown by Vite (typically http://localhost:5173). The frontend will connect to the backend WebSocket at `ws://localhost:5000/ws`.

## How It Works

- Backend captures audio from the default microphone at 16 kHz and feeds it to Vosk (`KaldiRecognizer`).
- When the backend recognizes words, it sends messages to all connected WebSocket clients.
- The wake word is `hey assistant`. After detection, the assistant enters `listening` state and asks a sequence of questions. You can reply by speaking (captured by the backend) or typing in the input box (sent as a WebSocket message).

## Messaging Protocol (WebSocket)

Endpoint: `ws://<host>:5000/ws`

Incoming messages from server:

- `{ "type": "state_change", "state": "idle" | "listening" | "processing" }`
- `{ "type": "transcript", "text": string }` — live recognized text
- `{ "type": "assistant_question", "text": string }` — assistant prompts
- `{ "type": "user_answer", "text": string }` — user replies as echoed by server

Outgoing messages from client:

- `{ "type": "text_input", "text": string }` — send a typed response during `listening` state

## Customization

- Wake word: edit `wake_word` in `backend/server.py`.
- Questions: edit the `questions` array in `backend/server.py`.
- Model: change `MODEL_URL` in `backend/model_downloader.py` to download a different Vosk model, or manually place an extracted model in `backend/model/`.

## Production Notes

- Frontend build: `cd frontend && npm run build` produces `frontend/dist/`. Serve it with any static server (Nginx, S3, etc.). The backend does not currently serve the frontend.
- Backend hosting: the backend reads from the machine's microphone. In production scenarios you typically run the backend on the same machine as the mic, or re-architect to stream audio from the browser to the backend (not implemented here).

## Troubleshooting

- PyAudio on Windows:
  - If `pip install pyaudio` fails, try installing a prebuilt wheel via `pipwin`:
    ```pwsh
    pip install pipwin
    pipwin install pyaudio
    ```
- No microphone input:
  - Ensure a default recording device is enabled in Windows Sound Settings.
  - Run the terminal as the same user with mic permissions.
- Port already in use:
  - Backend uses port 5000. Stop other services or run `python server.py` after setting an alternate port in code.
- Frontend can't connect:
  - Confirm backend is running and reachable at `ws://localhost:5000/ws`.
  - Check firewall rules and that both processes run on the same machine/network.

## Scripts & Commands

- Backend
  - `python backend/model_downloader.py` — downloads and unzips a Vosk model into `backend/model/`.
  - `python backend/server.py` — starts FastAPI + WebSocket server with Vosk recognizer.
- Frontend
  - `npm run dev` — development server with HMR.
  - `npm run build` — production build.
  - `npm run preview` — preview the production build locally.

## License

This project bundles no third-party model weights by default. Vosk models are downloaded from Alpha Cephei per their licenses. Review the model license before redistribution.
