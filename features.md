# features.md

## Application Features

- **Voice Calls with AI:** Accepts incoming phone calls via Twilio and provides an AI-powered assistant over the call.
- **Speech-to-Text:** Uses Whisper (OpenAI) to transcribe caller speech to text.
- **OpenAI Agent:** Sends the transcribed text to an OpenAI Agents SDK-based assistant to generate a response.
- **Text-to-Speech:** Converts the AI’s text response to speech (using OpenAI TTS or a similar service) and plays it back to the caller.
- **Real-time Streaming:** Processes audio in real-time using Twilio Media Streams and FastAPI WebSockets.
- **Storage & Logging:** Saves call audio and a structured JSON transcript to Google Cloud Storage for record-keeping.
- **API Endpoints:** A FastAPI backend with documented endpoints (`/incoming-call`, `/media-stream`) and Swagger UI enabled.
- **Containerized Deployment:** Packaged in Docker for consistent deployment.
- **CI/CD Pipeline:** Automated testing, building, and deployment via GitHub Actions (push to GCR, deploy to GCE).
- **Infrastructure as Code:** GCP resources (Compute VM, networking, Storage bucket) provisioned via Terraform.

## Architecture

The system architecture connects Twilio’s voice infrastructure to our FastAPI service. Twilio streams the call audio over a secure WebSocket. The FastAPI service uses an OpenAI voice agent pipeline: it performs speech-to-text on the incoming audio, queries an AI model, and synthesizes the spoken reply. Audio and transcripts are stored in GCP. The application runs in a Docker container on a GCP VM (with free-tier usage), behind appropriate firewall rules and load balancing for scalability.

## Endpoints and Usage

- `POST /incoming-call`: Twilio webhook for new calls. Returns TwiML with `<Connect><Stream>` to start media streaming.
- `WebSocket /media-stream`: Receives real-time audio from Twilio, processes it via the voice agent, and streams audio responses back.
- Swagger UI available at `/docs` for exploring/testing the API.

## Technology Stack

- **FastAPI:** Web framework (Python) with auto-generated OpenAPI docs:contentReference[oaicite:20]{index=20}.
- **Twilio Programmable Voice:** Telephony platform for call handling and media streaming:contentReference[oaicite:21]{index=21}.
- **OpenAI Agents SDK:** Agent framework for LLM-based dialogue:contentReference[oaicite:22]{index=22}:contentReference[oaicite:23]{index=23}.
- **Docker:** Containerizes the app for deployment.
- **Terraform:** Automates GCP infrastructure provisioning.
- **GitHub Actions:** CI/CD pipeline for building and deploying the application.
- **Google Cloud:** Deployment and storage (Compute Engine f1-micro, Cloud Storage bucket). GCP free tier covers 1 VM instance and 5GB storage:contentReference[oaicite:24]{index=24}.

## Development and Testing

- The app can be run locally with `uvicorn main:app`. Use ngrok to expose it to Twilio for testing.
- Unit tests can be added (e.g. pytest) and run in the CI pipeline.
- Logs and transcripts should be monitored to ensure correct AI behavior.

