import os
import sys
import json
import queue
import threading
import asyncio
import pyaudio
from vosk import Model, KaldiRecognizer
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audio Configuration
MIC_RATE = 16000
CHUNK = 8000
model_path = "model"

if not os.path.exists(model_path):
    print(f"Please download the model from https://alphacephei.com/vosk/models and unpack as '{model_path}' in the current folder.")
    sys.exit(1)

print("Loading model...", flush=True)
model = Model(model_path)
print("Model loaded.", flush=True)

audio_queue = queue.Queue()

# Assistant State
class AssistantState:
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"

current_state = AssistantState.IDLE
wake_word = "hey assistant"

questions = [
    "How are you feeling today?",
    "What is your favorite color?",
    "Do you like coding?"
]
current_question_index = -1

# Global event loop reference
main_loop = None

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

def audio_callback(in_data, frame_count, time_info, status):
    audio_queue.put(in_data)
    return (None, pyaudio.paContinue)

def broadcast_sync(message):
    if main_loop and main_loop.is_running():
        asyncio.run_coroutine_threadsafe(manager.broadcast(message), main_loop)

def speech_recognition_loop():
    global current_state, current_question_index
    
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=MIC_RATE, input=True, frames_per_buffer=CHUNK, stream_callback=audio_callback)
    stream.start_stream()

    rec = KaldiRecognizer(model, MIC_RATE)
    
    print("Assistant started. Listening...", flush=True)

    while True:
        data = audio_queue.get()
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text = result.get("text", "")
            
            if text:
                print(f"Recognized: {text}", flush=True)
                broadcast_sync({'type': 'transcript', 'text': text})

                if current_state == AssistantState.IDLE:
                    if wake_word in text.lower():
                        print("Wake word detected!", flush=True)
                        current_state = AssistantState.LISTENING
                        broadcast_sync({'type': 'state_change', 'state': current_state})
                        
                        current_question_index = 0
                        ask_question(questions[current_question_index])

                elif current_state == AssistantState.LISTENING:
                    print(f"User answered: {text}", flush=True)
                    broadcast_sync({'type': 'user_answer', 'text': text})
                    
                    current_question_index += 1
                    if current_question_index < len(questions):
                        ask_question(questions[current_question_index])
                    else:
                        finish_conversation()

def ask_question(question):
    print(f"Assistant asking: {question}", flush=True)
    broadcast_sync({'type': 'assistant_question', 'text': question})

def finish_conversation():
    global current_state, current_question_index
    print("Conversation finished.", flush=True)
    broadcast_sync({'type': 'assistant_question', 'text': "Thank you! Have a great day."})
    current_state = AssistantState.IDLE
    current_question_index = -1
    broadcast_sync({'type': 'state_change', 'state': current_state})

@app.on_event("startup")
async def startup_event():
    global main_loop
    main_loop = asyncio.get_running_loop()
    
    # Start audio thread
    t = threading.Thread(target=speech_recognition_loop, daemon=True)
    t.start()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Send initial state
    await websocket.send_json({'type': 'state_change', 'state': current_state})
    
    try:
        while True:
            data = await websocket.receive_json()
            # Handle text input from client
            if data.get('type') == 'text_input':
                text = data.get('text', '')
                handle_text_input(text)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

def handle_text_input(text):
    global current_state, current_question_index
    print(f"Received text input: {text}", flush=True)
    
    if current_state == AssistantState.LISTENING:
        broadcast_sync({'type': 'user_answer', 'text': text})
        current_question_index += 1
        if current_question_index < len(questions):
            ask_question(questions[current_question_index])
        else:
            finish_conversation()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
