FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install system dependencies for Playwright headless Chromium, PyMuPDF, & tini init
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    wget \
    gnupg \
    ca-certificates \
    libglib2.0-0 \
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
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies with caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

# Copy application source code (controlled by .dockerignore)
COPY . .

# Non-root container security: Create unprivileged user appuser:1000 & set ownership
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /ms-playwright

USER appuser

EXPOSE 8000

# Container healthcheck: validates endpoint /api/health with 30s interval
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4)" || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "app.py"]
