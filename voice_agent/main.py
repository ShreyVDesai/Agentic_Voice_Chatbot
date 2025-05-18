# # main.py

# import os
# import json
# import base64
# import uuid
# import logging
# from fastapi import FastAPI, WebSocket, Request, Response, WebSocketDisconnect
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
# from twilio.twiml.voice_response import VoiceResponse, Connect, Stream, Say
# from dotenv import load_dotenv
# from agents import Agent, Runner
# from agents.voice import VoicePipeline, VoiceWorkflowBase
# from google.cloud import storage, texttospeech
# from google.api_core.exceptions import GoogleAPIError
# from google.cloud import speech
# # from voice_pipeline import transcribe_audio  # Your Whisper or ASR module
# from workflows.combined import route_and_run        # Agentic combined workflow

# # --- Environment Setup ---
# load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
# TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
# GCP_PROJECT = os.getenv("GCP_PROJECT")
# TRANSCRIPTS_BUCKET = os.getenv("TRANSCRIPTS_BUCKET")

# # --- Validation ---
# required_vars = {
#     "OPENAI_API_KEY": OPENAI_API_KEY,
#     "TWILIO_ACCOUNT_SID": TWILIO_SID,
#     "TWILIO_AUTH_TOKEN": TWILIO_TOKEN,
#     "GCP_PROJECT": GCP_PROJECT,
#     "TRANSCRIPTS_BUCKET": TRANSCRIPTS_BUCKET
# }
# missing = [key for key, value in required_vars.items() if not value]
# if missing:
#     raise EnvironmentError(f"Missing environment variables: {', '.join(missing)}")

# # --- Logging Setup ---
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("voice-agent")

# # --- FastAPI Initialization ---
# app = FastAPI(title="Voice AI Agent", version="1.0")

# # --- CORS for testing / local dev ---
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # tighten in prod
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # --- Agent & Workflow ---
# agent = Agent(
#     name="VoiceAssistant",
#     instructions="You are a helpful AI assistant that talks clearly and informatively."
# )

# class VoiceResult:
#     def __init__(self, text, audio=None):
#         self.text = text
#         self.audio = audio
#         self.metadata = type("Metadata", (), {
#             "input_text": text,
#             "output_text": text
#         })()


# class MyVoiceWorkflow(VoiceWorkflowBase):
#     async def run(self, user_text: str) -> VoiceResult:
#         user_text = inputs.text
#         logger.info(f"[Agent Input] {user_text}")
#         ai_resp = Runner.run_sync(agent, user_text).final_output
#         logger.info(f"[Agent Response] {ai_resp}")
#         return VoiceResult(text=ai_resp)

# voice_pipeline = VoicePipeline(workflow=MyVoiceWorkflow())

# # --- GCS Setup ---
# try:
#     storage_client = storage.Client(project=GCP_PROJECT)
#     bucket = storage_client.bucket(TRANSCRIPTS_BUCKET)
# except GoogleAPIError as e:
#     logger.error("Failed to connect to Google Cloud Storage: %s", str(e))
#     raise
# # Speech setup
# speech_client = speech.SpeechClient()

# # --- Helpers ---
# def transcribe_audio(audio_bytes: bytes) -> str:
#     audio = speech.RecognitionAudio(content=audio_bytes)
#     config = speech.RecognitionConfig(
#         encoding=speech.RecognitionConfig.AudioEncoding.MULAW,
#         sample_rate_hertz=8000,  # Twilio typically streams in 8kHz mu-law
#         language_code="en-US"
#     )
#     try:
#         response = speech_client.recognize(config=config, audio=audio)
#         if response.results:
#             return response.results[0].alternatives[0].transcript
#         else:
#             return ""
#     except Exception as e:
#         logger.warning(f"STT failed: {e}")
#         return ""

# tts_client = texttospeech.TextToSpeechClient()

# def synthesize_audio(text: str) -> bytes:
#     input_text = texttospeech.SynthesisInput(text=text)
#     voice = texttospeech.VoiceSelectionParams(
#         language_code="en-US",
#         ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
#     )
#     audio_config = texttospeech.AudioConfig(
#         audio_encoding=texttospeech.AudioEncoding.MULAW,  # Required by Twilio
#         sample_rate_hertz=8000  # Required by Twilio
#     )

#     try:
#         response = tts_client.synthesize_speech(
#             input=input_text,
#             voice=voice,
#             audio_config=audio_config
#         )
#         return response.audio_content
#     except Exception as e:
#         # Optional: fallback or logging
#         import logging
#         logging.getLogger("voice-agent").error(f"TTS synthesis failed: {str(e)}")
#         return b''

# # --- Routes ---

# @app.get("/health", tags=["Health"])
# async def health_check():
#     return JSONResponse(status_code=200, content={"status": "ok"})

# @app.post("/incoming-call", tags=["Twilio"])
# async def incoming_call(request: Request):
#     """Handles Twilio webhook and returns TwiML to start streaming"""
#     try:
#         response = VoiceResponse()
#         response.say("Connecting you to the AI voice assistant.")
#         connect = Connect()
#         connect.append(Stream(url=f"wss://{request.url.hostname}/media-stream"))
#         response.append(connect)
#         return Response(content=str(response), media_type="application/xml")
#     except Exception as e:
#         logger.exception("Error generating TwiML")
#         return JSONResponse(status_code=500, content={"error": "Failed to generate TwiML"})

# @app.websocket("/media-stream")
# async def media_stream(ws: WebSocket):
#     await ws.accept()
#     session_id = str(uuid.uuid4())
#     transcript = []
#     all_audio = bytearray()

#     try:
#         while True:
#             message = await ws.receive_text()
#             event = json.loads(message)

#             if event["event"] == "media":
#                 audio_chunk = base64.b64decode(event["media"]["payload"])
#                 all_audio.extend(audio_chunk)

#                 # 1) Transcribe
#                 text = transcribe_audio(audio_chunk)
#                 if not text:
#                     continue
#                 logging.info(f"ASR: {text}")

#                 # 2) Route & run agentic workflow
#                 try:
#                     agent_result = await route_and_run(text)
#                     response_text = agent_result.final_output
#                 except Exception as e:
#                     logging.warning(f"Agent error: {e}")
#                     response_text = "Sorry, I couldn't process that."

#                 transcript.append({"input": text, "output": response_text})

#                 # 3) Synthesize
#                 audio_out = synthesize_audio(response_text)
#                 if audio_out:
#                     payload = base64.b64encode(audio_out).decode()
#                     await ws.send_json({
#                         "event": "media",
#                         "streamSid": event["streamSid"],
#                         "media": {"payload": payload}
#                     })

#             elif event["event"] == "stop":
#                 logging.info("Call ended, cleaning up.")
#                 break

#     except WebSocketDisconnect:
#         logging.warning("WebSocket disconnected unexpectedly.")
#     except Exception as e:
#         logging.exception("Unexpected error in media stream.")

#     finally:
#         await ws.close()
#         # Persist audio + transcript to GCS
#         try:
#             bucket.blob(f"sessions/{session_id}.wav") \
#                   .upload_from_string(bytes(all_audio), content_type="audio/wav")
#             bucket.blob(f"sessions/{session_id}.json") \
#                   .upload_from_string(json.dumps(transcript, indent=2),
#                                       content_type="application/json")
#             logging.info(f"Session {session_id} stored in GCS.")
#         except GoogleAPIError as e:
#             logging.error(f"GCS upload failed: {e}")

# main.py

import os
import json
import base64
import uuid
import logging
from fastapi import FastAPI, WebSocket, Request, Response, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from dotenv import load_dotenv
from agents.voice import VoicePipeline, VoiceWorkflowBase
from google.cloud import storage, texttospeech
from google.api_core.exceptions import GoogleAPIError
from google.cloud import speech
from workflows.combined import route_and_run  # ✅ Your unified agentic workflow

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

# --- GCS Setup ---
try:
    storage_client = storage.Client(project=GCP_PROJECT)
    bucket = storage_client.bucket(TRANSCRIPTS_BUCKET)
except GoogleAPIError as e:
    logger.error("Failed to connect to Google Cloud Storage: %s", str(e))
    raise

speech_client = speech.SpeechClient()

# --- TTS ---
tts_client = texttospeech.TextToSpeechClient()

def synthesize_audio(text: str) -> bytes:
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MULAW,
        sample_rate_hertz=8000
    )
    try:
        response = tts_client.synthesize_speech(
            input=input_text,
            voice=voice,
            audio_config=audio_config
        )
        return response.audio_content
    except Exception as e:
        logger.error(f"TTS synthesis failed: {str(e)}")
        return b''

def transcribe_audio(audio_bytes: bytes) -> str:
    audio = speech.RecognitionAudio(content=audio_bytes)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MULAW,
        sample_rate_hertz=8000,
        language_code="en-US"
    )
    try:
        response = speech_client.recognize(config=config, audio=audio)
        if response.results:
            return response.results[0].alternatives[0].transcript
        else:
            return ""
    except Exception as e:
        logger.warning(f"STT failed: {e}")
        return ""

# --- Voice Workflow ---

class VoiceResult:
    def __init__(self, text, audio=None):
        self.text = text
        self.audio = audio
        self.metadata = type("Metadata", (), {
            "input_text": text,
            "output_text": text
        })()

class MyVoiceWorkflow(VoiceWorkflowBase):
    async def run(self, user_text: str) -> VoiceResult:
        logger.info(f"[Agent Input] {user_text}")
        try:
            agent_result = await route_and_run(user_text)
            ai_resp = agent_result.final_output
        except Exception as e:
            logger.warning(f"[Agent Error] {e}")
            ai_resp = "Sorry, I couldn't process that."
        logger.info(f"[Agent Response] {ai_resp}")
        return VoiceResult(text=ai_resp)

voice_pipeline = VoicePipeline(workflow=MyVoiceWorkflow())

# --- Routes ---

@app.get("/health", tags=["Health"])
async def health_check():
    return JSONResponse(status_code=200, content={"status": "ok"})

@app.post("/incoming-call", tags=["Twilio"])
async def incoming_call(request: Request):
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
                audio_chunk = base64.b64decode(event["media"]["payload"])
                all_audio.extend(audio_chunk)

                text = transcribe_audio(audio_chunk)
                if not text:
                    continue
                logging.info(f"ASR: {text}")

                try:
                    agent_result = await route_and_run(text)
                    response_text = agent_result.final_output
                except Exception as e:
                    logging.warning(f"Agent error: {e}")
                    response_text = "Sorry, I couldn't process that."

                transcript.append({"input": text, "output": response_text})

                audio_out = synthesize_audio(response_text)
                if audio_out:
                    payload = base64.b64encode(audio_out).decode()
                    await ws.send_json({
                        "event": "media",
                        "streamSid": event["streamSid"],
                        "media": {"payload": payload}
                    })

            elif event["event"] == "stop":
                logging.info("Call ended, cleaning up.")
                break

    except WebSocketDisconnect:
        logging.warning("WebSocket disconnected unexpectedly.")
    except Exception as e:
        logging.exception("Unexpected error in media stream.")
    finally:
        await ws.close()
        try:
            bucket.blob(f"sessions/{session_id}.wav") \
                  .upload_from_string(bytes(all_audio), content_type="audio/wav")
            bucket.blob(f"sessions/{session_id}.json") \
                  .upload_from_string(json.dumps(transcript, indent=2),
                                      content_type="application/json")
            logging.info(f"Session {session_id} stored in GCS.")
        except GoogleAPIError as e:
            logging.error(f"GCS upload failed: {e}")
