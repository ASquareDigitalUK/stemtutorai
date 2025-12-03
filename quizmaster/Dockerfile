# Quizmaster Dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# requirements.txt is in the SAME folder as Dockerfile now
COPY requirements.txt /app/requirements.txt

# Copy the quizmaster service code (everything in this folder)
COPY . /app/quizmaster

RUN pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 8080

CMD ["uvicorn", "quizmaster.quizmaster_agent_service:app", "--host", "0.0.0.0", "--port", "8080"]