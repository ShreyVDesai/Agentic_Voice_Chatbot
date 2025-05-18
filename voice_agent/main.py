# main.py

import os
import json
import base64
import uuid
import time
import logging
import webrtcvad
from collections import deque

from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from twilio.twiml.voice_response import VoiceResponse, Start, Stream
from twilio.rest import Client
from google.cloud import storage, texttospeech, speech
from google.api_core.exceptions import GoogleAPIError
from dotenv import load_dotenv

from workflows.combined import route_and_run  # your agent pipeline

from gtts import gTTS
from pydub import AudioSegment
import io

# ─── Logging Setup ────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-agent")

# ─── Environment ───────────────────────────────────────────────────────────────
load_dotenv()
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY")
TWILIO_SID        = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN      = os.getenv("TWILIO_AUTH_TOKEN")
GCP_PROJECT       = os.getenv("GCP_PROJECT")
TRANSCRIPTS_BUCKET= os.getenv("TRANSCRIPTS_BUCKET")

missing = [k for k,v in {
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "TWILIO_SID": TWILIO_SID,
    "TWILIO_TOKEN": TWILIO_TOKEN,
    "GCP_PROJECT": GCP_PROJECT,
    "TRANSCRIPTS_BUCKET": TRANSCRIPTS_BUCKET,
}.items() if not v]
if missing:
    logger.error(f"Missing vars: {missing}")
    raise EnvironmentError(f"Missing vars: {missing}")

# ─── FastAPI & CORS ────────────────────────────────────────────────────────────
app = FastAPI(title="Voice AI Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# ─── Google Cloud Clients ─────────────────────────────────────────────────────
storage_client = storage.Client(project=GCP_PROJECT)
bucket = storage_client.bucket(TRANSCRIPTS_BUCKET)
speech_client = speech.SpeechClient()
tts_client    = texttospeech.TextToSpeechClient()

# ─── Twilio REST Client ───────────────────────────────────────────────────────
twilio_client = Client(TWILIO_SID, TWILIO_TOKEN)

# ─── VAD Setup ────────────────────────────────────────────────────────────────
vad = webrtcvad.Vad(2)
SAMPLE_RATE = 8000
FRAME_DURATION_MS = 20
FRAME_BYTES = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)

# ─── Helpers ──────────────────────────────────────────────────────────────────
def synthesize_audio(text: str) -> bytes:
    inp = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    cfg = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MULAW,
        sample_rate_hertz=8000
    )
    resp = tts_client.synthesize_speech(input=inp, voice=voice, audio_config=cfg)

    # Remove WAV header (first 58 bytes)
    # mulaw_audio = resp.audio_content[44:]

    # return mulaw_audio
    return resp


def transcribe_audio(audio_bytes: bytes) -> str:
    audio = speech.RecognitionAudio(content=audio_bytes)
    cfg = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MULAW,
        sample_rate_hertz=SAMPLE_RATE,
        language_code="en-US"
    )
    resp = speech_client.recognize(config=cfg, audio=audio)
    if resp.results:
        return resp.results[0].alternatives[0].transcript
    return ""

def is_speech(frame: bytes) -> bool:
    if len(frame) != FRAME_BYTES:
        return False
    return vad.is_speech(frame, SAMPLE_RATE)

# ─── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})

@app.post("/incoming-call")
async def incoming_call(request: Request):
    """Welcome and redirect to start streaming."""
    logger.info("Incoming call received")
    resp = VoiceResponse()
    resp.say("Welcome to the AI assistant. Please wait…", voice="Polly.Joanna")
    resp.redirect("/start-stream")
    return Response(content=str(resp), media_type="application/xml")

@app.post("/start-stream")
async def start_stream(request: Request):
    """Begin media stream and hold call open."""
    logger.info("Starting media stream")
    resp = VoiceResponse()
    start = Start()
    start.stream(url=f"wss://{request.url.hostname}/media-stream")
    resp.append(start)
    resp.pause(length=60)  # initial hold
    return Response(content=str(resp), media_type="application/xml")

@app.websocket("/media-stream")
async def media_stream(ws: WebSocket):
    """
    Bidirectional voice loop:
      - Receive inbound chunks until silence → transcribe → agent → reply
      - Use Twilio REST API to play reply and re-start stream
    """
    await ws.accept()
    session_id = str(uuid.uuid4())
    logger.info(f"WS session {session_id} started")

    full_audio = bytearray()
    speech_buffer = bytearray()
    last_speech = time.time()
    transcript = []

    SILENCE_FRAMES = int((1.5 * 1000) / FRAME_DURATION_MS)

    # We need the call SID from the Twilio start event
    call_sid = None

    try:
        while True:
            msg = await ws.receive_text()
            ev = json.loads(msg)

            # Capture call SID on 'start' event
            if ev["event"] == "start" and not call_sid:
                call_sid = ev["start"]["callSid"]
                logger.info(f"Call SID: {call_sid}")

            if ev["event"] == "media":
                chunk = base64.b64decode(ev["media"]["payload"])
                full_audio.extend(chunk)

                # Frame‑level VAD
                for i in range(0, len(chunk), FRAME_BYTES):
                    frame = chunk[i:i+FRAME_BYTES]
                    if len(frame) < FRAME_BYTES: break

                    if is_speech(frame):
                        last_speech = time.time()
                        speech_buffer.extend(frame)
                    # else, silence frame

                # If user paused long enough, process
                if speech_buffer and (time.time() - last_speech) > 1.5:
                    audio_bytes = bytes(speech_buffer)
                    speech_buffer.clear()

                    # Transcribe
                    user_text = transcribe_audio(audio_bytes)
                    if not user_text.strip():
                        last_speech = time.time()
                        continue

                    logger.info(f"Transcribed: {user_text}")

                    # Agentic response
                    try:
                        agent_res = await route_and_run(user_text)
                        reply = agent_res.final_output
                    except Exception as e:
                        logger.error(e)
                        reply = "Sorry, I couldn't process that."

                    logger.info(f"Replying: {reply}")
                    transcript.append({"input": user_text, "output": reply})
                    out_bytes = synthesize_audio(reply)
                    
                    await ws.send_json({"event": "media","media": {"payload": base64.b64encode(out_bytes).decode()}})
                    # Send reply via Twilio REST and re‑start stream
                    # twilio_client.calls(call_sid).update(
                    #     twiml=(
                    #         "<Response>"
                    #           f"<Say>{reply}</Say>"
                    #           "<Start><Stream "
                    #             f"url='wss://{ws.scope['server'][0]}/media-stream'/>"
                    #           "</Start>"
                    #         "</Response>"
                    #     )
                    # )
                    last_speech = time.time()

            elif ev["event"] == "stop":
                logger.info("Stop event: ending")
                break

    except WebSocketDisconnect:
        logger.warning("WebSocket disconnected")
    finally:
        # Clean up
        try: await ws.close()
        except: pass
        # Upload
        bucket.blob(f"sessions/{session_id}.wav") \
              .upload_from_string(bytes(full_audio), content_type="audio/wav")
        bucket.blob(f"sessions/{session_id}.json") \
              .upload_from_string(json.dumps(transcript), content_type="application/json")
        logger.info(f"Session {session_id} complete")

