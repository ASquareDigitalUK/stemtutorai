# Quizmaster Dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the *service* as a package named "quizmaster"
COPY . /app/quizmaster

# (optional, but nice) show what’s there during build
RUN ls -R /app

EXPOSE 8080

# Run the FastAPI app inside the quizmaster package
CMD ["uvicorn", "quizmaster.quizmaster_agent_service:app", "--host", "0.0.0.0", "--port", "8080"]
