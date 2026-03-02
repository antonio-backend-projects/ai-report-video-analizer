# Quick Start

Up and running in 5 minutes.

---

## Prerequisites

- [ ] Python 3.10 or higher
- [ ] ffmpeg installed on your system
- [ ] Anthropic account with an active API key

---

## Step 1 — Clone the repository

```bash
git clone https://github.com/hp/ai-report-video-analizer.git
cd ai-report-video-analizer
```

---

## Step 2 — Install Python dependencies

```bash
pip install -r requirements.txt
```

---

## Step 3 — Install ffmpeg

=== "Windows"

    ```bash
    winget install ffmpeg
    ```

    Open a **new** terminal after installation.

=== "macOS"

    ```bash
    brew install ffmpeg
    ```

=== "Linux"

    ```bash
    sudo apt install ffmpeg
    ```

Verify:

```bash
ffmpeg -version
```

---

## Step 4 — Configure the API key

```bash
cp .env.example .env
```

Open `.env` and insert your key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

!!! tip "Where do I find the API key?"
    Go to [console.anthropic.com](https://console.anthropic.com) → **API Keys** → **Create Key**.

---

## Step 5 — Add a video

Copy a video file to the `videos/` folder:

```bash
cp /path/to/your/video.mp4 videos/
```

Supported formats: `.mp4` `.avi` `.mkv` `.mov` `.webm` `.flv`

---

## Step 6 — Run the analysis

```bash
python analyze_video.py
```

Or for a specific video:

```bash
python analyze_video.py videos/video.mp4
```

!!! note "Windows — special characters"
    If you see encoding errors on Windows, run with:
    ```bash
    python -X utf8 analyze_video.py
    ```

---

## What you will see

```
============================================================
  VIDEO: video.mp4
============================================================
  Duration: 120.0s  |  Estimated frames: 120  |  FPS: 1.0

[1/3] Extracting frames with ffmpeg...
  Running ffmpeg...
  Extracted 120 frames

[2/3] Describing frames with Claude Vision...
  Total frames: 120  |  Batch size: 10
  Batch 1/12: 10 frames...
  Batch 2/12: 10 frames...
  ...
  Descriptions saved -> output/video_descriptions.txt

[3/3] Analyzing process with Claude...

## 1. PROCESS OBJECTIVE
...

  Analysis saved -> output/video_analysis.md
  Temporary frames removed
```

---

## Results

Files are saved in `output/`:

```
output/
├── video_descriptions.txt    ← frame-by-frame descriptions
└── video_analysis.md         ← structured process report
```

---

!!! success "Done!"
    See the **[Usage](utilizzo.md)** section for all available options.
