FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY multi_bot_trading_system_vision0.0.1.3/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY multi_bot_trading_system_vision0.0.1.3/backend/ ./backend/

# Copy .env.example and .env handling
COPY multi_bot_trading_system_vision0.0.1.3/.env.example ./.env.example

# Expose the dashboard port
EXPOSE 5000

# Create non-root user
RUN useradd -m -u 1000 appuser
USER appuser

# Start the API-only server
CMD ["python", "-m", "backend.api_only"]