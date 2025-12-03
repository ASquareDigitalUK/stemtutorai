FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy everything INCLUDING your static agent-card.json
COPY . /app

EXPOSE 8080

CMD ["uvicorn", "quizmaster_agent_service:app", "--host", "0.0.0.0", "--port", "8080"]