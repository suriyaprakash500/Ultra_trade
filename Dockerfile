FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/
COPY tests/ ./tests/
COPY logs/ ./logs/

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8000

# Run the server
CMD ["python", "-m", "backend.main"]
