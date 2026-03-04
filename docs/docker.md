# Docker

Run the analyzer in a container without installing Python or ffmpeg locally.

---

## Overview

The Docker setup provides:

- **Isolated environment** — Python, ffmpeg, and Whisper dependencies pre-installed
- **Local output** — `videos/` and `output/` are mounted from your local filesystem
- **Whisper model cache** — Docker volumes persist downloaded models between runs
- **Flexible Whisper backend** — choose at build time via `WHISPER_BACKEND`

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- `.env` file configured (copy from `.env.example`)

---

## Quick start

### 1. Configure `.env`

```bash
cp .env.example .env
# Edit .env with your API keys and Whisper backend
```

Minimum required:
```env
ANTHROPIC_API_KEY=sk-ant-...
WHISPER_BACKEND=faster-whisper
WHISPER_MODEL=large-v3
```

### 2. Build the image

```bash
docker compose build
```

This installs ffmpeg, Python dependencies, and the selected Whisper backend.

!!! tip "Rebuild after changing WHISPER_BACKEND"
    The Whisper backend is baked into the image at build time.
    If you change `WHISPER_BACKEND` in `.env`, rebuild: `docker compose build`.

### 3. Add videos

```bash
cp /path/to/your/video.mp4 videos/
```

### 4. Run analysis

```bash
# Analyze all videos in videos/
docker compose run --rm analyzer

# Analyze a specific video
docker compose run --rm analyzer videos/mio.mp4

# With audio transcription
docker compose run --rm analyzer videos/mio.mp4 --audio

# Audio-only mode
docker compose run --rm analyzer videos/meeting.mp4 --audio-only

# Override Whisper model at runtime
docker compose run --rm analyzer --audio --whisper-model medium
```

Output files appear in your local `output/` folder immediately.

---

## Build options

### Selecting the Whisper backend

The backend is set via `ARG WHISPER_BACKEND` in the `Dockerfile`. By default it reads `WHISPER_BACKEND` from `.env`:

```bash
# Build with faster-whisper (default, ~1.5 GB image)
docker compose build

# Build with openai-whisper (includes PyTorch, ~4-5 GB image)
docker compose build --build-arg WHISPER_BACKEND=openai-whisper

# Build without local Whisper (for openai-api backend)
docker compose build --build-arg WHISPER_BACKEND=openai-api
```

### Image sizes

| Backend | Approximate image size |
|---|---|
| `faster-whisper` | ~1.5 GB |
| `openai-whisper` | ~4–5 GB |
| `openai-api` | ~500 MB |

---

## Volume mounts

The `docker-compose.yml` mounts:

| Local path | Container path | Mode | Purpose |
|---|---|---|---|
| `./videos/` | `/app/videos` | read-only | Input videos |
| `./output/` | `/app/output` | read-write | Analysis results |
| Docker volume | `/root/.cache/huggingface` | read-write | faster-whisper model cache |
| Docker volume | `/root/.cache/whisper` | read-write | openai-whisper model cache |

!!! important "Output stays local"
    All files in `output/` are written directly to your local filesystem, not inside the container.
    The container is ephemeral — you can remove it without losing any results.

---

## First run — model download

On the first run with a local Whisper backend, the model is downloaded automatically:

```
[whisper] Carico modello 'large-v3' (faster-whisper)...
# First time: downloads ~1.5 GB from HuggingFace
# Subsequent runs: loads from Docker volume cache
```

The download is cached in a named Docker volume (`whisper_cache_hf` or `whisper_cache_openai`), so subsequent runs start immediately.

---

## Common commands

```bash
# Build (or rebuild after code/dependency changes)
docker compose build

# Run analysis on all videos
docker compose run --rm analyzer

# Run with specific flags
docker compose run --rm analyzer videos/mio.mp4 --fps 2 --audio --keep-frames

# View the output
ls output/

# Show logs from last run
docker compose logs

# Remove containers (output is safe — it's on local filesystem)
docker compose down

# Remove containers AND cached Whisper models (frees disk space)
docker compose down -v
```

---

## GPU acceleration

By default, the container runs Whisper on CPU. To enable GPU (NVIDIA):

1. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
2. Add to `docker-compose.yml`:

```yaml
services:
  analyzer:
    # ... existing config ...
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - WHISPER_DEVICE=cuda
```

3. Rebuild the image with GPU-compatible packages.

---

## Troubleshooting

### "Cannot connect to Docker daemon"

Docker Desktop is not running. Start it from your Applications/taskbar.

### Output folder is empty after run

Check that `./output/` exists on your local machine before running:
```bash
mkdir -p output videos
```

### Build fails — disk space

The `openai-whisper` image can be 4-5 GB. Ensure you have at least 10 GB free.
Use `faster-whisper` or `openai-api` for a lighter image.

### Slow on CPU

Whisper `large-v3` is slow on CPU. Options:
- Use `--whisper-model medium` or `--whisper-model small` for faster (less accurate) transcription
- Use `WHISPER_BACKEND=openai-api` to offload transcription to the cloud
- Enable GPU acceleration (see above)
