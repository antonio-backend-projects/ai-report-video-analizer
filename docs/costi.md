# API Costs

Estimated costs for using the tool. Costs depend on the mode selected.

---

## Claude Opus 4.6 pricing (Anthropic)

| Token type | Price |
|---|---|
| Input | $5.00 / 1M tokens |
| Output | $25.00 / 1M tokens |

*Prices as of March 2026. Check [anthropic.com/pricing](https://anthropic.com/pricing) for updates.*

---

## OpenAI Whisper API pricing (openai-api backend only)

| Item | Price |
|---|---|
| Transcription | $0.006 / minute of audio |

*Applies only when `WHISPER_BACKEND=openai-api`. The `faster-whisper` and `openai-whisper` backends run locally and have no API cost.*

---

## Cost per step

### Step 1 — Audio (optional, `--audio` or `--audio-only`)

| Backend | Cost |
|---|---|
| `faster-whisper` (local) | $0 — runs on your machine |
| `openai-whisper` (local) | $0 — runs on your machine |
| `openai-api` | $0.006 × video duration in minutes |

**Claude transcript refinement** (all backends):
~2,000–10,000 input tokens (transcript length) + ~2,000 output tokens.
Estimated: **$0.06–$0.35** depending on video length.

### Step 2 — Frame description (Vision)

Cost depends on the number of frames and their visual complexity.

**Estimate per frame** (average values):

| Item | Average tokens |
|---|---|
| PNG image (1080p) | ~1,500 input |
| Batch text prompt | ~200 input |
| Description response | ~100 output |

**Approximate formula:**

```
Step 2 cost ≈ N_frames × (1,700 input + 100 output) tokens
            ≈ N_frames × (0.0085 + 0.0025) $
            ≈ N_frames × $0.0011
```

### Step 3 — Process analysis

| Item | Average tokens |
|---|---|
| Prompt + descriptions (+ transcript if --audio) | ~N_frames × 50 + transcript length |
| Generated report | ~3,000–5,000 output |

---

## Cost table by mode

### Visual only (default)

| Video length | FPS | Frames | Step 2 | Step 3 | **Total** |
|---|---|---|---|---|---|
| 2 minutes | 1 | 120 | ~$0.13 | ~$0.09 | ~**$0.22** |
| 5 minutes | 1 | 300 | ~$0.33 | ~$0.10 | ~**$0.43** |
| 5 minutes | 2 | 600 | ~$0.66 | ~$0.11 | ~**$0.77** |
| 10 minutes | 1 | 600 | ~$0.66 | ~$0.11 | ~**$0.77** |
| 10 minutes | 2 | 1,200 | ~$1.32 | ~$0.12 | ~**$1.44** |
| 20 minutes | 1 | 1,200 | ~$1.32 | ~$0.12 | ~**$1.44** |
| 20 minutes | 0.5 | 600 | ~$0.66 | ~$0.11 | ~**$0.77** |

### With `--audio` (openai-api backend)

Adds Whisper API cost + Claude refinement to the visual cost above.

| Video length | Whisper API | Claude refinement | Additional cost |
|---|---|---|---|
| 5 minutes | ~$0.03 | ~$0.08 | ~**+$0.11** |
| 10 minutes | ~$0.06 | ~$0.10 | ~**+$0.16** |
| 30 minutes | ~$0.18 | ~$0.15 | ~**+$0.33** |
| 60 minutes | ~$0.36 | ~$0.20 | ~**+$0.56** |

*Using local backend (`faster-whisper`): Whisper API cost = $0. Only Claude refinement applies.*

### `--audio-only` (no Vision API)

| Video length | Whisper API | Claude refinement | Claude analysis | **Total** |
|---|---|---|---|---|
| 5 minutes | ~$0.03 | ~$0.08 | ~$0.09 | ~**$0.20** |
| 10 minutes | ~$0.06 | ~$0.10 | ~$0.10 | ~**$0.26** |
| 30 minutes | ~$0.18 | ~$0.15 | ~$0.12 | ~**$0.45** |
| 60 minutes | ~$0.36 | ~$0.20 | ~$0.15 | ~**$0.71** |

*With local Whisper backend: subtract Whisper API cost from the total.*

!!! note "Approximate values"
    Actual tokens vary based on visual density (frames with text cost more),
    speech density, and transcript length.

---

## Strategies to reduce costs

### 1. Lower the FPS

```bash
python analyze_video.py --fps 0.5   # halves the number of frames
```

Use `0.5` for long videos or with slow actions (e.g., system waits, static screens).

### 2. Use `--audio-only` when visuals are not needed

```bash
python analyze_video.py videos/meeting.mp4 --audio-only
```

Eliminates Vision API costs entirely. Ideal for meetings, webinars, voice tutorials.

### 3. Use a local Whisper backend

```bash
# .env
WHISPER_BACKEND=faster-whisper
```

Eliminates Whisper API cost ($0.006/min). Requires one-time model download (~1.5 GB for large-v3).

### 4. Increase batch-size

```bash
python analyze_video.py --batch-size 20
```

Reduces the number of API calls (less overhead), but does not change total token count.

### 5. Reuse descriptions and transcripts

If you only need to change the analysis prompt, **do not delete** the `_descrizioni.txt` or `_trascrizione.txt` files.
Those steps will be automatically skipped on the next run.

### 6. Use Sonnet for descriptions

Modify `MODEL` in `analyze_video.py`:
- **Sonnet** for step 2 (frame descriptions): sufficient quality, ~40% lower cost
- **Opus** for step 3 (analysis): maximum quality where it matters

### 7. Test on short clips

Before processing a long video, test with a 2-3 minute sample to verify
the quality meets expectations.

---

## Cost monitoring

From the Anthropic dashboard:

- [console.anthropic.com/usage](https://console.anthropic.com/usage) — token usage by date
- [console.anthropic.com/settings/limits](https://console.anthropic.com/settings/limits) — set a monthly spending limit

From the OpenAI dashboard (if using openai-api backend):

- [platform.openai.com/usage](https://platform.openai.com/usage) — Whisper API usage and costs

!!! tip "Set a spending limit"
    Both Anthropic and OpenAI consoles let you configure a **monthly budget**
    that blocks requests when the limit is reached. Useful for development environments.
