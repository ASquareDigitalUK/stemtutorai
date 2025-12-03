# Quizmaster Dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt

# Copy only the code (NOT the .well-known agent-card.json)
COPY . /app/quizmaster

# Remove any static agent-card.json that was accidentally copied
RUN rm -rf /app/quizmaster/.well-known/agent-card.json

# Keep template
COPY quizmaster/.well-known/agent-card-template.json /app/.well-known/agent-card-template.json

RUN pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 8080

# Generate runtime agent-card.json (using Cloud Run ENV var)
CMD ["sh", "-c", "\
mkdir -p /app/.well-known && \
envsubst < /app/.well-known/agent-card-template.json > /app/.well-known/agent-card.json && \
uvicorn quizmaster.quizmaster_agent_service:app --host 0.0.0.0 --port 8080 \
"]