# AI Report Video Analyzer

A Python tool that analyzes screen recordings using **Claude Vision** and **Whisper**, and automatically generates **structured process reports**.

---

## How it works

=== "Visual only (default)"

    ```
    VIDEO.mp4
       │
       ▼  [ffmpeg]
    Extracts 1 frame/second
       │
       ▼  [Claude Vision — claude-opus-4-6]
    Describes each frame: UI, user actions, messages, state changes
       │
       ▼  [Claude Opus — adaptive thinking, effort=high]
    Analyzes the full chronological flow → structured report
       │
       ▼
    output/
     ├── video_descrizioni.txt    ← frame-by-frame visual transcript
     └── video_analisi.md         ← structured report (5 sections)
    ```

=== "Visual + Audio (--audio)"

    ```
    VIDEO.mp4
       │
       ├──── [ffmpeg] → audio → [Whisper] → raw transcript
       │                                          │
       │                              [Claude] refines transcript
       │                                          │
       ▼  [ffmpeg]                                │
    Extracts frames                               │
       │                                          │
       ▼  [Claude Vision]                         │
    Frame descriptions ────────────────────────────┘
                               │
                     [Claude Opus] analyzes
                     visual + audio together
                               │
                               ▼
    output/
     ├── video_descrizioni.txt
     ├── video_trascrizione.txt    ← corrected audio transcript
     └── video_analisi.md          ← report enriched with audio
    ```

=== "Audio only (--audio-only)"

    ```
    VIDEO.mp4
       │
       ▼  [ffmpeg]
    Extracts audio → WAV mono 16kHz
       │
       ▼  [Whisper — 3 backends available]
    Transcribes speech → raw text
       │
       ▼  [Claude]
    Corrects hallucinations, formats text
       │
       ▼  [Claude Opus — adaptive thinking, effort=high]
    Summary + structured text analysis
       │
       ▼
    output/
     ├── video_trascrizione.txt    ← clean corrected transcript
     └── video_audio_analisi.md   ← summary + text report
    ```

---

## What it produces

| Mode | Output |
|---|---|
| Default | Frame-by-frame descriptions + 5-section process report |
| `--audio` | All of the above + corrected audio transcript integrated into analysis |
| `--audio-only` | Clean transcript + summary + text-only structured report |

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API key
cp .env.example .env
# edit .env with your ANTHROPIC_API_KEY

# 3. Place videos in videos/

# 4. Run (visual analysis)
python analyze_video.py

# Run with audio transcription
python analyze_video.py --audio

# Transcribe and analyze audio only (no Vision API)
python analyze_video.py --audio-only
```

Results saved to `output/`.

---

## Technologies

| Component | Technology |
|---|---|
| Frame extraction | ffmpeg |
| Audio extraction + compression | ffmpeg |
| Audio transcription | Whisper (faster-whisper / openai-whisper / OpenAI API) |
| Vision AI | Claude Opus 4.6 (Vision) |
| Transcript refinement | Claude Opus 4.6 |
| Process analysis | Claude Opus 4.6 (adaptive thinking, effort=high) |
| SDK | anthropic (Python) |

---

## Navigation

- **[Quick Start](quickstart.md)** — Up and running in 5 minutes
- **[How it works](architettura.md)** — Detailed technical pipeline
- **[Usage](utilizzo.md)** — All commands and options
- **[Audio Transcription](audio.md)** — Whisper backends, models, audio-only mode
- **[Docker](docker.md)** — Run without local Python/ffmpeg installation
- **[Output](output.md)** — Format of generated files
- **[Examples](esempi.md)** — Real analyses with report excerpts
- **[API Costs](costi.md)** — Cost estimates per video and mode
- **[Troubleshooting](troubleshooting.md)** — Solutions to common errors
