# Audio Transcription

Complete guide to audio transcription with Whisper.

---

## Overview

The audio feature uses **Whisper** (by OpenAI) to transcribe speech from videos, then **Claude** to:

1. Correct transcription errors and hallucinations
2. Integrate the transcript into the process analysis (with `--audio`)
3. Generate a standalone text-based report (with `--audio-only`)

Audio transcription is **opt-in** — it does not activate unless you use `--audio` or `--audio-only`.

---

## Three backends

You can choose between three transcription backends, configured via `.env`:

=== "faster-whisper (Recommended)"

    **Local, CTranslate2-based.** The fastest and most resource-efficient local option.

    ```bash
    pip install faster-whisper
    ```

    ```env
    WHISPER_BACKEND=faster-whisper
    WHISPER_MODEL=large-v3
    ```

    | Pro | Con |
    |---|---|
    | 4x faster than openai-whisper | Requires CTranslate2 installation |
    | Low RAM usage | Results may differ slightly from the official model |
    | No PyTorch required | |
    | Works on CPU without CUDA | |

=== "openai-whisper (Official)"

    **Local, PyTorch-based.** The original reference implementation from OpenAI.

    ```bash
    pip install openai-whisper
    ```

    ```env
    WHISPER_BACKEND=openai-whisper
    WHISPER_MODEL=large-v3
    ```

    | Pro | Con |
    |---|---|
    | Official OpenAI implementation | Requires PyTorch (~2 GB download) |
    | Reference quality | Slower than faster-whisper |
    | Works offline | Large disk footprint |

=== "openai-api (Cloud)"

    **No local installation.** Calls the OpenAI Whisper API. No GPU or heavy dependencies needed.

    ```bash
    pip install openai
    ```

    ```env
    WHISPER_BACKEND=openai-api
    WHISPER_MODEL=whisper-1
    OPENAI_API_KEY=sk-...
    ```

    | Pro | Con |
    |---|---|
    | No local model download | Requires OPENAI_API_KEY |
    | Works on any machine | API cost (~$0.006/min) |
    | Consistent quality | Requires internet connection |
    | Best for machines with limited RAM | |

    !!! info "Nessun limite di durata"
        Prima dell'invio, il file audio viene automaticamente compresso in **mp3 mono 32 kbps**
        (qualità ottimale per il parlato, ~18x più piccolo del WAV).
        Se il file compresso supera comunque 25 MB (video > ~104 minuti), lo script
        **suddivide automaticamente in chunk da 10 minuti**, trascrive ciascuno e
        concatena i risultati. Nessun limite pratico di durata.

---

## Model sizes (local backends)

| Model | Download size | RAM usage | Speed | Quality |
|---|---|---|---|---|
| `tiny` | ~39 MB | ~1 GB | Very fast | Basic |
| `base` | ~74 MB | ~1 GB | Fast | Good |
| `small` | ~244 MB | ~2 GB | Medium | Better |
| `medium` | ~769 MB | ~5 GB | Slow | High |
| `large-v3` | ~1.5 GB | ~10 GB | Very slow | Best |

!!! tip "Which model to choose?"
    For most use cases: **`large-v3`** for maximum accuracy.
    If you have limited RAM or need speed: **`medium`** or **`small`**.
    For quick tests: **`base`**.

The model can be overridden at runtime:
```bash
python analyze_video.py --audio --whisper-model medium
```

---

## Usage modes

### `--audio` — Visual + Audio

Full pipeline: frame descriptions **and** audio transcript, integrated into a single report.

```bash
python analyze_video.py videos/tutorial.mp4 --audio
```

**Output:**
```
output/
├── tutorial_descrizioni.txt      ← frame-by-frame visual transcript
├── tutorial_trascrizione.txt     ← corrected audio transcript
└── tutorial_analisi.md           ← process report (visual + audio)
```

Use when: the video shows an operator doing things AND explaining what they're doing.

---

### `--audio-only` — Audio only

Skips the visual pipeline entirely. No frames extracted, no Vision API calls.

```bash
python analyze_video.py videos/meeting.mp4 --audio-only
```

**Output:**
```
output/
├── meeting_trascrizione.txt      ← corrected audio transcript
└── meeting_audio_analisi.md      ← structured text analysis
```

The audio report contains:

| Section | Content |
|---|---|
| **1. Sommario esecutivo** | 3-5 sentence summary of the video |
| **2. Struttura del contenuto** | Main topics in order of appearance |
| **3. Elementi tecnici e terminologia** | Technical terms, acronyms, product names |
| **4. Azioni e decisioni identificate** | Action items, decisions, next steps |
| **5. Osservazioni sulla comunicazione** | Clarity, gaps, improvement suggestions |

Use when: the video is a meeting, webinar, voice tutorial, or any content where speech is primary.

---

## Claude transcript refinement

After Whisper transcribes the audio, Claude automatically:

- Removes common Whisper hallucinations (repeated phrases, invented closing statements)
- Adds punctuation and proper sentence structure
- Divides text into logical paragraphs where context changes

Claude does **not** add, invent, or interpret content not present in the original transcript.

!!! info "Very long transcripts"
    If the raw transcript exceeds ~80,000 characters (approx. 60+ minutes of speech),
    the Claude refinement step is skipped and the raw Whisper output is saved directly.
    This avoids hitting token limits.

---

## Transcript caching

The corrected transcript is saved to `output/<name>_trascrizione.txt`.

On subsequent runs, if this file exists, **Whisper transcription is skipped** — Claude reads the existing transcript directly. This mirrors the frame descriptions caching behavior.

To force re-transcription, delete the `_trascrizione.txt` file:
```bash
rm output/mio_video_trascrizione.txt
```

---

## Troubleshooting

### "Nessuna traccia audio trovata nel video"

The video has no audio stream. Use the tool without `--audio`.

### "WHISPER_BACKEND=... non valido"

Check that `WHISPER_BACKEND` in `.env` is one of: `openai-whisper`, `faster-whisper`, `openai-api`.

### "OPENAI_API_KEY non trovata"

When using `WHISPER_BACKEND=openai-api`, add your OpenAI key to `.env`:
```
OPENAI_API_KEY=sk-...
```

### Slow transcription on CPU

Switch to a smaller model:
```bash
python analyze_video.py --audio --whisper-model small
```

Or use `WHISPER_BACKEND=openai-api` for cloud transcription with no local compute.

### Poor transcription quality

- Use a larger model: `--whisper-model large-v3`
- Ensure the audio is clear (check with a media player)
- `faster-whisper` and `openai-whisper` may differ slightly — try both if quality is an issue
