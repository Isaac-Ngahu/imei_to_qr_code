FROM python:3.11-slim

# =========================
# System dependencies for Playwright
# =========================
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libglib2.0-0 \
    fonts-liberation \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# =========================
# Install Playwright + Chromium
# =========================
RUN pip install playwright
RUN playwright install --with-deps chromium

# =========================
# Gunicorn server
# =========================
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:8080"]