# ================================
# Base Image
# ================================
FROM python:3.11-slim

# ================================
# Setup working directory
# ================================
WORKDIR /app

# ================================
# 1. Install system dependencies (AS ROOT) 🛠️
# This must happen before switching to the non-root user.
# build-essential is added back for compiling gRPC/other dependencies.
# ================================
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    # Clean up APT cache to keep the image size down
    && rm -rf /var/lib/apt/lists/*

# ================================
# 2. Setup non-root user (Security Best Practice)
# ================================
RUN useradd -m appuser

# ================================
# 3. Install Python dependencies (Optimized Caching)
# Copy requirements first, so changes to code don't invalidate this layer.
# ================================
COPY requirements.txt .

# Use the default root user for pip installation to avoid permission issues
# but the resulting files will be owned by root, which is fine for the build phase.
RUN pip install --no-cache-dir -r requirements.txt

# ================================
# 4. Switch to non-root user (Runtime Security)
# ================================
USER appuser

# ================================
# 5. Copy application code
# The --chown ensures the non-root user owns the code.
# ================================
COPY --chown=appuser:appuser . .

# ================================
# Cloud Run configuration
# ================================
ENV PORT=8080
EXPOSE 8080

# ================================
# Start the FastAPI app (Run as appuser)
# ================================
# Removed 'bash -c' wrapper for cleaner CMD execution
CMD uvicorn app.fastapi_server:app --host 0.0.0.0 --port ${PORT}
