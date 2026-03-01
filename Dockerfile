FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8000

# Render sets PORT env var — use shell form so $PORT is expanded
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
