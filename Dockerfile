FROM python:3.11-slim
# Install system dependencies if needed (for voice libraries)
RUN apt-get update && apt-get install -y ffmpeg
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Expose port (Twilio requires HTTPS, so we'll use a reverse proxy or Cloud Run)
EXPOSE 8000
# Run the FastAPI app with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
