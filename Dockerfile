FROM node:20-slim AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# --- Python Backend ---
FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt requests requests-oauthlib greenlet

# Copy backend code
COPY backend/ ./

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist ./frontend_dist

# Create articles directory
RUN mkdir -p ./articles

# Environment
ENV PYTHONUNBUFFERED=1
ENV ARTICLES_DIR=./articles
ENV FRONTEND_DIST_DIR=./frontend_dist

EXPOSE 8000

CMD ["python", "run.py"]
