# Quizmaster Dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV QUIZMASTER_URL=${QUIZMASTER_URL}

# Install system deps + envsubst
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gettext-base && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy project into a package path: /app/quizmaster
COPY . /app/quizmaster

# Make sure it's a proper Python package
RUN touch /app/quizmaster/__init__.py

# Ensure .well-known exists and template is present
RUN mkdir -p /app/quizmaster/.well-known
RUN test -f /app/quizmaster/.well-known/agent-card-template.json

EXPOSE 8080

# Generate agent-card.json at runtime using QUIZMASTER_URL
CMD ["sh", "-c", "\
envsubst < /app/quizmaster/.well-known/agent-card-template.json > /app/quizmaster/.well-known/agent-card.json && \
uvicorn quizmaster.quizmaster_agent_service:app --host 0.0.0.0 --port ${PORT:-8080} \
"]