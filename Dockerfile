FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Hermes Agent for real E2E execution
RUN pip install --no-cache-dir hermes-agent>=0.21.0

# Copy application code (backend module at /app/backend/, worker at /app/worker.py)
COPY backend/ /app/backend/
COPY backend/worker.py /app/worker.py

# For real E2E: Hermes is installed on host; in production, this container
# requires the hermes binary available on PATH (installed in base image or mounted)
# The adapter uses self.hermes_bin (default: "hermes") and checks availability.
# For this environment, hermes is available at /home/yellowdeerco/.local/bin/hermes
# and /home/yellowdeerco/.hermes/hermes-agent/venv/bin/hermes

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Expose port
EXPOSE 8000

# Run the backend application
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]