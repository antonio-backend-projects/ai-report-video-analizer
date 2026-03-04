# Usage

## Main commands

### Analyze all videos in `videos/`

```bash
python analyze_video.py
```

Processes all `.mp4 .avi .mkv .mov .webm .flv` files found in the `videos/` folder sequentially.

---

### Analyze a specific video

```bash
python analyze_video.py videos/my_video.mp4
```

---

## Options

| Option | Default | Description |
|---|---|---|
| `--fps` | `1.0` | Frames extracted per second |
| `--batch-size` | `10` | Frames sent per Vision API call |
| `--keep-frames` | off | Save PNG screenshots to `output/frames/` |
| `--audio` | off | Enable Whisper transcription + integrate into analysis |
| `--audio-only` | off | Skip vision pipeline: transcribe audio + text analysis only |
| `--whisper-model` | from `.env` | Override Whisper model size at runtime |

---

### `--fps` — analysis detail

Controls how many frames per second are extracted from the video.

```bash
# 1 frame per second (default, good for most cases)
python analyze_video.py --fps 1

# 2 frames per second (more detail, slower and more expensive)
python analyze_video.py --fps 2

# 1 frame every 2 seconds (faster, less detail)
python analyze_video.py --fps 0.5
```

!!! tip "How many fps to use?"
    - **Software tutorials / UX flows**: 1 fps is ideal
    - **Fast processes with many actions**: use 2 fps
    - **Long videos (>10 min)**: use 0.5 fps to save costs

---

### `--batch-size` — batch size

How many frames are sent in a single API call to Claude Vision.

```bash
# Batch of 5 frames (uses fewer tokens per call)
python analyze_video.py --batch-size 5

# Batch of 20 frames (fewer API calls, but more tokens per call)
python analyze_video.py --batch-size 20
```

!!! info "When to reduce the batch?"
    If the video has frames with dense information (small text, complex UI),
    reduce the batch to 5 to give Claude more "room" to analyze each frame.

---

### `--keep-frames` — save screenshots

```bash
python analyze_video.py --keep-frames
```

Saves all extracted PNG screenshots to:
```
output/frames/<video_name>/
  ├── frame_0001.png   (t=0s)
  ├── frame_0002.png   (t=1s)
  └── ...
```

Useful to visually verify which frames were analyzed.

---

### `--audio` — audio transcription + integration

Enables Whisper audio transcription. The corrected transcript is integrated alongside the visual frame descriptions in the final analysis, giving Claude both visual and spoken context.

```bash
python analyze_video.py videos/tutorial.mp4 --audio
```

Requires a Whisper backend installed and `WHISPER_BACKEND` configured in `.env`.
See [Audio Transcription](audio.md) for setup.

**Additional output:** `output/<name>_trascrizione.txt`

---

### `--audio-only` — transcription + text analysis, no Vision

Skips the visual pipeline entirely. No frames are extracted, no Vision API calls are made.

```bash
python analyze_video.py videos/meeting.mp4 --audio-only
```

Pipeline: audio extraction → Whisper transcription → Claude refinement → Claude text analysis.

**Output:** `output/<name>_trascrizione.txt` + `output/<name>_audio_analisi.md`

!!! tip "Use for spoken content"
    Ideal for meetings, webinars, training videos, narrated tutorials — any video where
    the spoken content carries more information than the screen visuals.

---

### `--whisper-model` — override Whisper model

Overrides the `WHISPER_MODEL` value from `.env` at runtime, without editing the config file.

```bash
python analyze_video.py --audio --whisper-model medium
python analyze_video.py --audio-only --whisper-model base
```

| Model | Size | Quality |
|---|---|---|
| `tiny` | ~39 MB | Basic |
| `base` | ~74 MB | Good |
| `small` | ~244 MB | Better |
| `medium` | ~769 MB | High |
| `large-v3` | ~1.5 GB | Best |
| `whisper-1` | cloud | High (openai-api backend only) |

---

## Combined examples

```bash
# Specific video, 2fps, with saved screenshots
python analyze_video.py videos/tutorial.mp4 --fps 2 --keep-frames

# All videos, fast visual analysis (0.5fps)
python analyze_video.py --fps 0.5

# Long video with small batches for more accuracy
python analyze_video.py videos/long.mp4 --fps 1 --batch-size 5 --keep-frames

# Full analysis: visual + audio integrated
python analyze_video.py videos/tutorial.mp4 --audio

# Meeting recording: audio-only transcript + text analysis
python analyze_video.py videos/meeting.mp4 --audio-only

# Audio-only with faster model for quick tests
python analyze_video.py videos/meeting.mp4 --audio-only --whisper-model base

# Full pipeline: high detail visual + high quality audio
python analyze_video.py videos/training.mp4 --fps 2 --audio --whisper-model large-v3
```

---

## Runtime output

### Visual only (default)

```
============================================================
  VIDEO: tutorial.mp4
============================================================
  Duration: 245.3s  |  Estimated frames: 245  |  FPS: 1.0

[1/3] Estrazione frame con ffmpeg...
  Eseguendo ffmpeg...
  Estratti 245 frame

[2/3] Descrizione frame con Claude Vision...
  Totale frame: 245  |  Batch da: 10
  Batch 1/25: 10 frame...
  ...
  Descrizioni salvate -> output/tutorial_descrizioni.txt

[3/3] Analisi del processo con Claude...
------------------------------------------------------------
## 1. OBIETTIVO DEL PROCESSO
[real-time streaming output...]
------------------------------------------------------------
  Analisi salvata -> output/tutorial_analisi.md
  File temporanei rimossi
```

### With `--audio`

```
[1/4] Estrazione e trascrizione audio...
  Trascrizione audio con backend 'faster-whisper', modello 'large-v3'...
  [whisper] Carico modello 'large-v3' (faster-whisper)...
  Raffinamento trascrizione con Claude...
  Trascrizione salvata -> output/tutorial_trascrizione.txt

[2/4] Estrazione frame con ffmpeg...
[3/4] Descrizione frame con Claude Vision...
[4/4] Analisi del processo con Claude...
  Analisi salvata -> output/tutorial_analisi.md
```

### With `--audio-only`

```
[1/2] Estrazione e trascrizione audio...
  Compressione audio → mp3 32k (parlato)...
  Dimensione mp3: 1.4 MB
  Trascrizione audio con backend 'openai-api', modello 'whisper-1'...
  Raffinamento trascrizione con Claude...
  Trascrizione salvata -> output/meeting_trascrizione.txt

[2/2] Analisi audio con Claude...
------------------------------------------------------------
## 1. SOMMARIO ESECUTIVO
[real-time streaming output...]
------------------------------------------------------------
  Analisi audio salvata -> output/meeting_audio_analisi.md
  File temporanei rimossi
```

!!! note "Description reuse"
    If `_descrizioni.txt` or `_trascrizione.txt` already exist, those steps are
    automatically skipped. This lets you rerun only the analysis without re-paying
    for Vision or Whisper API calls.
