# Tutor Dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt

COPY . /app/tutor

# CRITICAL FIX — remove accidentally copied agent-card
RUN rm -rf /app/tutor/.well-known

RUN pip install --no-cache-dir -r /app/requirements.txt

CMD ["sh", "-c", "uvicorn tutor.agent_entrypoint:app --host 0.0.0.0 --port ${PORT}"]