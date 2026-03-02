# CLI Reference

Complete documentation of all commands and flags.

---

## Syntax

```bash
python analyze_video.py [VIDEO] [--fps FPS] [--batch-size N] [--keep-frames]
```

---

## Arguments

### `VIDEO` *(optional)*

Path to the video to analyze. If omitted, analyzes all videos in `videos/`.

```bash
# Analyze all videos in videos/
python analyze_video.py

# Analyze a specific video
python analyze_video.py videos/my_video.mp4

# With absolute path
python analyze_video.py /home/user/recordings/session.mp4
```

**Supported formats:** `.mp4` `.avi` `.mkv` `.mov` `.webm` `.flv`

---

## Flags

### `--fps FPS`

**Default:** `1.0`
**Type:** float
**Constraints:** `0.1 <= fps <= 30`

Frames per second to extract from the video.

```bash
python analyze_video.py --fps 1     # 1 frame/second (default)
python analyze_video.py --fps 2     # 2 frames/second
python analyze_video.py --fps 0.5   # 1 frame every 2 seconds
python analyze_video.py --fps 0.25  # 1 frame every 4 seconds
```

---

### `--batch-size N`

**Default:** `10`
**Type:** int

Number of frames sent per Claude Vision API call.

```bash
python analyze_video.py --batch-size 5    # small batches
python analyze_video.py --batch-size 10   # default
python analyze_video.py --batch-size 20   # large batches
```

---

### `--keep-frames`

**Default:** disabled (boolean flag)

Saves PNG screenshots to `output/frames/<video_name>/` instead of deleting them.

```bash
python analyze_video.py --keep-frames
```

---

### `-h` / `--help`

Shows the help message.

```bash
python analyze_video.py --help
```

---

## Common combinations

```bash
# Specific video, standard analysis
python analyze_video.py videos/process.mp4

# Specific video, more detail, with screenshots
python analyze_video.py videos/process.mp4 --fps 2 --keep-frames

# Long video, less detail, cost saving
python analyze_video.py videos/long.mp4 --fps 0.5

# Dense UI (forms, tables), small batches for more accuracy
python analyze_video.py videos/crm.mp4 --fps 1 --batch-size 5 --keep-frames

# All videos in videos/, fast analysis
python analyze_video.py --fps 0.5

# Windows with special characters in output
python -X utf8 analyze_video.py videos/process.mp4
```

---

## Runtime output

During execution, 3 phases are shown:

```
============================================================
  VIDEO: process.mp4
============================================================
  Duration: 245.3s  |  Estimated frames: 245  |  FPS: 1.0

[1/3] Extracting frames with ffmpeg...
  Running ffmpeg...
  Extracted 245 frames

[2/3] Describing frames with Claude Vision...
  Total frames: 245  |  Batch size: 10
  Batch 1/25: 10 frames...
  Batch 2/25: 10 frames...
  ...
  Descriptions saved -> output/process_descriptions.txt

[3/3] Analyzing process with Claude...

------------------------------------------------------------
## 1. PROCESS OBJECTIVE
[real-time streaming output...]
------------------------------------------------------------

  Analysis saved -> output/process_analysis.md
  Temporary frames removed
```

!!! note "Description reuse"
    If the `_descriptions.txt` file already exists, phase `[2/3]` is automatically
    skipped. This allows regenerating only the analysis without re-paying for
    Vision API calls.

---

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Completed successfully |
| `1` | Error: ANTHROPIC_API_KEY missing |
| `1` | Error: ffmpeg not found |
| `1` | Error: video file not found |
| `1` | Error: unsupported video format |
| `1` | Error: fps out of range (0.1-30) |
| `1` | Error: videos/ folder not found |
