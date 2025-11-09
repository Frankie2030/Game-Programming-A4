FROM python:3.11-slim

# --- Environment Configuration ---
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    PORT=12345 \
    APP_HOME=/app

WORKDIR $APP_HOME

# --- Copy Project Files ---
COPY . $APP_HOME

# --- Install Dependencies ---
RUN apt-get update && apt-get install -y --no-install-recommends \
        netcat-openbsd \
        libglib2.0-0 \
        libgthread-2.0-0 \
        libsdl2-mixer-2.0-0 \
        libsdl2-image-2.0-0 \
        libsdl2-ttf-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip && \
    if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# --- Expose Server Port ---
EXPOSE ${PORT}

# --- Healthcheck (optional for ECS) ---
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD \
    nc -z localhost ${PORT} || exit 1

ENV SDL_AUDIODRIVER=dummy

# --- Start Dedicated Server ---
CMD ["python", "main.py", "--server", "--host", "0.0.0.0", "--port", "12345"]
