FROM node:22-alpine AS angular-builder

WORKDIR /app/frontend/angular

COPY ./frontend/angular/package.json ./frontend/angular/package-lock.json ./
RUN npm ci

COPY ./frontend/angular/angular.json ./frontend/angular/tsconfig*.json ./
COPY ./frontend/angular/.postcssrc.json ./
COPY ./frontend/angular/src ./src
COPY ./frontend/angular/public ./public
RUN npm run build

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt from project root
COPY ./requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
# Project root has backend/ directory, copy it to /app/backend
COPY ./backend ./backend
COPY --from=angular-builder /app/frontend/angular/dist/angular/browser ./frontend/angular/dist/angular/browser

# Copy .env.example from project root
COPY .env.example .env.example

# Expose the dashboard port (5000)
EXPOSE 5000

# Create non-root user
RUN useradd -m -u 1000 appuser \
    && mkdir -p /app/trades \
    && chown appuser:appuser /app/trades
USER appuser

# Start the API-only server
CMD ["python", "-m", "backend.api_only"]