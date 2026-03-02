# AI Report Video Analyzer

A Python tool that analyzes mute screen recordings using **Claude Vision** (claude-opus-4-6) and automatically generates a **structured process report**.

Ideal for:
- Analyzing operational workflows in CRM / ERP systems
- Automatic documentation of software tutorials
- UX audits on screen recordings
- Reverse engineering of business procedures

---

## How it works

```
VIDEO.mp4
   │
   ▼  [ffmpeg]
extracts 1 frame/second → frame_0001.png, frame_0002.png, ...
   │
   ▼  [Claude Vision — claude-opus-4-6]
describes each frame: interfaces, user actions, messages, state changes
   │
   ▼  [Claude Opus — adaptive thinking, effort=high]
analyzes the full chronological flow and generates the structured report
   │
   ▼
output/
 ├── video_descriptions.txt    ← frame-by-frame visual transcript
 └── video_analysis.md         ← structured report in 5 sections
```

---

## Output

The generated report contains 5 sections:

| Section | Content |
|---|---|
| **1. Process objective** | What the user/system is trying to accomplish |
| **2. Step-by-step operational flow** | Each action with the UI element involved and result |
| **3. Technical elements** | Systems, applications, data, visible technologies |
| **4. Critical observations** | Bottlenecks, errors, attention points |
| **5. Optimization suggestions** | Concrete improvements based on the observed process |

---

## Quick setup

### 1. ffmpeg (system tool)

```bash
# Windows (winget — included in Windows 11)
winget install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

### 2. Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Anthropic API key

```bash
cp .env.example .env
# open .env and set your ANTHROPIC_API_KEY
```

---

## Usage

```bash
# Analyze all videos in videos/
python analyze_video.py

# Analyze a specific video
python analyze_video.py videos/my_video.mp4

# 2 frames per second (more detail)
python analyze_video.py --fps 2

# Save PNG screenshots
python analyze_video.py --keep-frames

# Smaller batches (complex frames)
python analyze_video.py --batch-size 5
```

### Options

| Flag | Default | Description |
|---|---|---|
| `--fps` | `1.0` | Frames extracted per second |
| `--batch-size` | `10` | Frames per Claude Vision API call |
| `--keep-frames` | off | Save PNG screenshots to `output/frames/` |

---

## Folder structure

```
ai-report-video-analizer/
├── videos/                  ← place your videos here
├── output/                  ← results (created automatically)
│   ├── frames/              ← PNG screenshots (only with --keep-frames)
│   ├── *_descriptions.txt   ← frame-by-frame descriptions
│   └── *_analysis.md        ← structured report
├── docs/                    ← MkDocs documentation
├── analyze_video.py         ← main script
├── requirements.txt
├── mkdocs.yml
├── .env.example
└── .env                     ← API key (DO NOT commit)
```

---

## Supported video formats

`.mp4` `.avi` `.mkv` `.mov` `.webm` `.flv`

---

## Estimated API costs

| Video length | FPS | Frames | Estimated cost |
|---|---|---|---|
| 5 minutes | 1 | ~300 | ~$0.43 |
| 10 minutes | 1 | ~600 | ~$0.77 |
| 5 minutes | 2 | ~600 | ~$0.77 |

*Based on Claude Opus 4.6 pricing: $5/1M input tokens, $25/1M output tokens*

---

## Requirements

- Python 3.10+
- ffmpeg installed on the system
- Anthropic API key (with access to claude-opus-4-6)

---

## Full documentation

```bash
mkdocs serve
```

Open `http://127.0.0.1:8000`

---

## License

MIT
