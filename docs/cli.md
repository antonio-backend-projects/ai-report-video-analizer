# CLI Reference

Complete documentation of all commands and flags.

---

## Syntax

```bash
python analyze_video.py [VIDEO] [--fps FPS] [--batch-size N] [--keep-frames]
                        [--audio] [--audio-only] [--whisper-model MODEL]
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

### `--audio`

**Default:** disabled (boolean flag)

Enables Whisper audio transcription. The transcript is extracted, corrected by Claude, and integrated into the process analysis alongside the visual frame descriptions.

```bash
python analyze_video.py --audio
python analyze_video.py videos/tutorial.mp4 --audio
```

Requires `WHISPER_BACKEND` set in `.env` and the corresponding package installed.
See [Audio Transcription](audio.md) for setup details.

---

### `--audio-only`

**Default:** disabled (boolean flag)

Skips the visual pipeline entirely. Only transcribes audio and generates a text-based analysis (summary, content structure, key topics, actions/decisions).

```bash
python analyze_video.py --audio-only
python analyze_video.py videos/meeting.mp4 --audio-only
```

**Output:** `output/<name>_trascrizione.txt` + `output/<name>_audio_analisi.md`

!!! tip "Use for spoken content"
    Ideal for meetings, webinars, training videos, or any video where the spoken
    content carries more information than the visuals.

---

### `--whisper-model MODEL`

**Default:** `WHISPER_MODEL` from `.env` (default: `large-v3`)
**Type:** string

Overrides the Whisper model size at runtime without editing `.env`.

```bash
python analyze_video.py --audio --whisper-model medium
python analyze_video.py --audio-only --whisper-model base
```

| Model | Size | Speed | Quality |
|---|---|---|---|
| `tiny` | ~39 MB | Very fast | Basic |
| `base` | ~74 MB | Fast | Good |
| `small` | ~244 MB | Medium | Better |
| `medium` | ~769 MB | Slow | High |
| `large-v3` | ~1.5 GB | Very slow | Best |

For `openai-api` backend, use `whisper-1` (cloud model, size irrelevant).

---

### `-h` / `--help`

Shows the help message.

```bash
python analyze_video.py --help
```

---

## Common combinations

```bash
# Specific video, standard visual analysis
python analyze_video.py videos/process.mp4

# Specific video, more detail, with screenshots
python analyze_video.py videos/process.mp4 --fps 2 --keep-frames

# Long video, less detail, cost saving
python analyze_video.py videos/long.mp4 --fps 0.5

# Dense UI (forms, tables), small batches for more accuracy
python analyze_video.py videos/crm.mp4 --fps 1 --batch-size 5 --keep-frames

# Full analysis: visual frames + audio transcript integrated
python analyze_video.py videos/tutorial.mp4 --audio

# Audio-only: transcription + text analysis (fastest, no Vision API)
python analyze_video.py videos/meeting.mp4 --audio-only

# Audio-only with faster model (less accurate but quicker)
python analyze_video.py videos/meeting.mp4 --audio-only --whisper-model base

# All videos in videos/, fast visual analysis
python analyze_video.py --fps 0.5

# Windows with special characters in output
python -X utf8 analyze_video.py videos/process.mp4
```

---

## Runtime output

Phases shown depend on the mode selected:

- **Visual only** (default): 3 steps
- **--audio** (visual + audio): 4 steps
- **--audio-only**: 2 steps (audio extraction + audio analysis)

Example with `--audio`:

```
============================================================
  VIDEO: process.mp4
============================================================
  Duration: 245.3s  |  Estimated frames: 245  |  FPS: 1.0

[1/4] Estrazione e trascrizione audio...
  Trascrizione audio con backend 'faster-whisper', modello 'large-v3'...
  [whisper] Carico modello 'large-v3' (faster-whisper)...
  Raffinamento trascrizione con Claude...
  Trascrizione salvata -> output/process_trascrizione.txt

[2/4] Estrazione frame con ffmpeg...
  Eseguendo ffmpeg...
  Estratti 245 frame

[3/4] Descrizione frame con Claude Vision...
  Totale frame: 245  |  Batch da: 10
  Batch 1/25: 10 frame...
  Batch 2/25: 10 frame...
  ...
  Descrizioni salvate -> output/process_descrizioni.txt

[4/4] Analisi del processo con Claude...

------------------------------------------------------------
## 1. OBIETTIVO DEL PROCESSO
[output in streaming real-time...]
------------------------------------------------------------

  Analisi salvata -> output/process_analisi.md
  File temporanei rimossi
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
| `1` | Error: invalid WHISPER_BACKEND value |
| `1` | Error: OPENAI_API_KEY missing (openai-api backend) |
