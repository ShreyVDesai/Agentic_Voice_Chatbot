# main.py

import os
import json
import base64
import uuid
import logging
from fastapi import FastAPI, WebSocket, Request, Response, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream, Say
from dotenv import load_dotenv
from agents import Agent, Runner
from agents.voice import VoicePipeline, VoiceWorkflowBase, VoiceInput, VoiceResult
from google.cloud import storage
from google.api_core.exceptions import GoogleAPIError

# --- Environment Setup ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
GCP_PROJECT = os.getenv("GCP_PROJECT")
TRANSCRIPTS_BUCKET = os.getenv("TRANSCRIPTS_BUCKET")

# --- Validation ---
required_vars = {
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "TWILIO_ACCOUNT_SID": TWILIO_SID,
    "TWILIO_AUTH_TOKEN": TWILIO_TOKEN,
    "GCP_PROJECT": GCP_PROJECT,
    "TRANSCRIPTS_BUCKET": TRANSCRIPTS_BUCKET
}
missing = [key for key, value in required_vars.items() if not value]
if missing:
    raise EnvironmentError(f"Missing environment variables: {', '.join(missing)}")

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-agent")

# --- FastAPI Initialization ---
app = FastAPI(title="Voice AI Agent", version="1.0")

# --- CORS for testing / local dev ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Agent & Workflow ---
agent = Agent(
    name="VoiceAssistant",
    instructions="You are a helpful AI assistant that talks clearly and informatively."
)

class MyVoiceWorkflow(VoiceWorkflowBase):
    async def run(self, inputs: VoiceInput) -> VoiceResult:
        user_text = inputs.text
        logger.info(f"[Agent Input] {user_text}")
        ai_resp = Runner.run_sync(agent, user_text).final_output
        logger.info(f"[Agent Response] {ai_resp}")
        return VoiceResult(text=ai_resp)

voice_pipeline = VoicePipeline(workflow=MyVoiceWorkflow())

# --- GCS Setup ---
try:
    storage_client = storage.Client(project=GCP_PROJECT)
    bucket = storage_client.bucket(TRANSCRIPTS_BUCKET)
except GoogleAPIError as e:
    logger.error("Failed to connect to Google Cloud Storage: %s", str(e))
    raise

# --- Routes ---

@app.get("/health", tags=["Health"])
async def health_check():
    return JSONResponse(status_code=200, content={"status": "ok"})

@app.post("/incoming-call", tags=["Twilio"])
async def incoming_call(request: Request):
    """Handles Twilio webhook and returns TwiML to start streaming"""
    try:
        response = VoiceResponse()
        response.say("Connecting you to the AI voice assistant.")
        connect = Connect()
        connect.append(Stream(url=f"wss://{request.url.hostname}/media-stream"))
        response.append(connect)
        return Response(content=str(response), media_type="application/xml")
    except Exception as e:
        logger.exception("Error generating TwiML")
        return JSONResponse(status_code=500, content={"error": "Failed to generate TwiML"})

@app.websocket("/media-stream")
async def media_stream(ws: WebSocket):
    await ws.accept()
    session_id = str(uuid.uuid4())
    transcript = []
    all_audio = bytearray()

    try:
        while True:
            message = await ws.receive_text()
            event = json.loads(message)

            if event["event"] == "media":
                payload_b64 = event["media"]["payload"]
                audio_chunk = base64.b64decode(payload_b64)
                all_audio.extend(audio_chunk)

                try:
                    result: VoiceResult = await voice_pipeline.run(audio_chunk)
                except Exception as e:
                    logger.warning("Error in pipeline run: %s", str(e))
                    continue

                transcript.append({
                    "input_text": result.metadata.input_text,
                    "output_text": result.metadata.output_text
                })

                if result.audio:
                    try:
                        encoded_audio = base64.b64encode(result.audio).decode()
                        await ws.send_json({
                            "event": "media",
                            "streamSid": event["streamSid"],
                            "media": {"payload": encoded_audio}
                        })
                    except Exception as e:
                        logger.warning("Failed to send audio: %s", str(e))

            elif event["event"] == "stop":
                logger.info("Received stop event from Twilio.")
                break

    except WebSocketDisconnect:
        logger.warning("WebSocket disconnected unexpectedly")
    except Exception as e:
        logger.exception("Unhandled WebSocket error")
    finally:
        await ws.close()
        try:
            audio_blob = bucket.blob(f"{session_id}.wav")
            audio_blob.upload_from_string(bytes(all_audio), content_type="audio/wav")
            trans_blob = bucket.blob(f"{session_id}.json")
            trans_blob.upload_from_string(json.dumps(transcript, indent=2), content_type="application/json")
            logger.info(f"Uploaded session {session_id} to GCS.")
        except GoogleAPIError as e:
            logger.error("Failed to upload to GCS: %s", str(e))
