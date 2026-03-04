FROM python:3.11-slim

# Dipendenze di sistema: ffmpeg + build tools per faster-whisper/openai-whisper
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installa dipendenze Python core
RUN pip install --no-cache-dir \
    "anthropic>=0.40.0" \
    "python-dotenv>=1.0.0"

# Seleziona il backend Whisper al momento del build.
# Override: docker compose build --build-arg WHISPER_BACKEND=openai-whisper
# Nota: openai-whisper installa PyTorch (~2 GB) → immagine ~4-5 GB
#       faster-whisper usa CTranslate2 → immagine ~1.5 GB
#       openai-api non richiede dipendenze locali pesanti
ARG WHISPER_BACKEND=faster-whisper
RUN if [ "$WHISPER_BACKEND" = "faster-whisper" ]; then \
        pip install --no-cache-dir "faster-whisper>=1.0.0"; \
    elif [ "$WHISPER_BACKEND" = "openai-whisper" ]; then \
        pip install --no-cache-dir "openai-whisper>=20231117"; \
    elif [ "$WHISPER_BACKEND" = "openai-api" ]; then \
        pip install --no-cache-dir "openai>=1.0.0"; \
    fi

COPY analyze_video.py .

# Crea le directory di mount point (verranno sovrascritte dai volumi)
RUN mkdir -p /app/videos /app/output

ENTRYPOINT ["python", "analyze_video.py"]
