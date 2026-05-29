FROM node:20-slim AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --legacy-peer-deps
COPY frontend/src ./src
COPY frontend/index.html frontend/vite.config.js frontend/tailwind.config.js frontend/postcss.config.js ./
RUN npx vite build

# --- Python Backend ---
FROM python:3.12-slim

WORKDIR /app

# Install system deps (including Playwright/Chromium deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
    libpango-1.0-0 libcairo2 libasound2 libxshmfence1 \
    libxfixes3 libx11-xcb1 libxcb1 libx11-6 libxext6 libdbus-1-3 \
    fonts-liberation fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser
RUN playwright install chromium

# Copy backend code
COPY backend/ ./

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist ./frontend_dist

# Create persistent data directories
RUN mkdir -p /app/data/articles /app/data/trained_models /app/data/marketing_visuals

# Environment
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/app/data
ENV ARTICLES_DIR=/app/data/articles
ENV DATABASE_URL=sqlite+aiosqlite:////app/data/bot.db
ENV FRONTEND_DIST_DIR=./frontend_dist

EXPOSE 8000

CMD ["python", "run.py"]
