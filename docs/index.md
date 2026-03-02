# AI Report Video Analyzer

A Python tool that analyzes mute screen recordings using **Claude Vision** (claude-opus-4-6) and automatically generates a **structured process report**.

---

## How it works

```
VIDEO.mp4
   │
   ▼
[ffmpeg] extracts 1 frame/second
   │
   ▼
[Claude Vision] describes each frame (UI, user actions, messages)
   │
   ▼
[Claude Opus] analyzes the full flow and generates the report
   │
   ▼
output/
 ├── video_descriptions.txt   ← frame-by-frame visual transcript
 └── video_analysis.md        ← structured process report
```

---

## What it produces

Given a screen recording of any operation (software tutorial, UX flow, business process...), you get:

- **Frame-by-frame descriptions** — what appears in each second of the video
- **Analysis report** with:
    - Process objective
    - Step-by-step operational flow
    - Identified technical elements
    - Observations and bottlenecks
    - Optimization suggestions

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API key
cp .env.example .env
# edit .env with your ANTHROPIC_API_KEY

# 3. Place videos in videos/

# 4. Run
python analyze_video.py
```

Results saved to `output/`.

---

## Technologies

| Component | Technology |
|---|---|
| Frame extraction | ffmpeg |
| Vision AI | Claude Opus 4.6 (Vision) |
| Process analysis | Claude Opus 4.6 (adaptive thinking) |
| SDK | anthropic (Python) |

---

## Navigation

- **[Quick Start](quickstart.md)** — Up and running in 5 minutes
- **[How it works](architettura.md)** — Detailed technical pipeline
- **[Usage](utilizzo.md)** — All commands and options
- **[Output](output.md)** — Format of generated files
- **[Examples](esempi.md)** — Real analyses with report excerpts
- **[API Costs](costi.md)** — Cost estimates per video
- **[Troubleshooting](troubleshooting.md)** — Solutions to common errors
