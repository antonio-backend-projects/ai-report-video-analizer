# How it works

Technical description of the analysis pipeline.

---

## Full pipeline

=== "Visual only (default)"

    ```
    VIDEO.mp4
        │
        ▼
    ┌─────────────────────────────────────────┐
    │  STEP 1 — Frame extraction              │
    │  Tool: ffmpeg                           │
    │  Output: temp_frames/video/frame_*.png  │
    └─────────────────────────────────────────┘
        │
        ▼  (batches of N frames)
    ┌─────────────────────────────────────────┐
    │  STEP 2 — Frame description             │
    │  Model: claude-opus-4-6 (Vision)        │
    │  Output: text description per frame     │
    └─────────────────────────────────────────┘
        │
        ▼
    ┌─────────────────────────────────────────┐
    │  STEP 3 — Process analysis              │
    │  Model: claude-opus-4-6                 │
    │  Thinking: adaptive, effort=high        │
    │  Output: structured report (5 sections) │
    └─────────────────────────────────────────┘
        │
        ▼
    output/
    ├── video_descrizioni.txt
    └── video_analisi.md
    ```

=== "Visual + Audio (--audio)"

    ```
    VIDEO.mp4
        │
        ├──────────────────────┐
        ▼                      ▼
    ┌──────────────┐   ┌───────────────────────┐
    │  Frame       │   │  Audio extraction     │
    │  extraction  │   │  Tool: ffmpeg → WAV   │
    │  (ffmpeg)    │   └───────────────────────┘
    └──────────────┘               │
        │                          ▼
        │               ┌───────────────────────┐
        │               │  Whisper transcription │
        │               │  Backend: selectable   │
        │               └───────────────────────┘
        │                          │
        │                          ▼
        │               ┌───────────────────────┐
        │               │  Claude refines        │
        │               │  transcript            │
        │               └───────────────────────┘
        │                          │
        ▼  (batches)               │
    ┌──────────────┐               │
    │  Claude      │               │
    │  Vision      │               │
    │  description │               │
    └──────────────┘               │
        │                          │
        └──────────┬───────────────┘
                   ▼
    ┌─────────────────────────────────────────┐
    │  Process analysis (visual + audio)      │
    │  Model: claude-opus-4-6                 │
    │  Thinking: adaptive, effort=high        │
    └─────────────────────────────────────────┘
        │
        ▼
    output/
    ├── video_descrizioni.txt
    ├── video_trascrizione.txt
    └── video_analisi.md
    ```

=== "Audio only (--audio-only)"

    ```
    VIDEO.mp4
        │
        ▼
    ┌─────────────────────────────────────────┐
    │  Audio extraction                       │
    │  Tool: ffmpeg → WAV mono 16kHz          │
    └─────────────────────────────────────────┘
        │
        ▼
    ┌─────────────────────────────────────────┐
    │  Whisper transcription                  │
    │  Backend: openai-whisper | faster-      │
    │           whisper | openai-api          │
    └─────────────────────────────────────────┘
        │
        ▼
    ┌─────────────────────────────────────────┐
    │  Claude: transcript refinement          │
    │  Fix hallucinations, punctuation        │
    └─────────────────────────────────────────┘
        │
        ▼
    ┌─────────────────────────────────────────┐
    │  Claude: audio analysis                 │
    │  Summary + structure + observations     │
    │  Thinking: adaptive, effort=high        │
    └─────────────────────────────────────────┘
        │
        ▼
    output/
    ├── video_trascrizione.txt
    └── video_audio_analisi.md
    ```

---

## Step 1 — Frame extraction

Uses **ffmpeg** via Python subprocess to extract PNG frames from the video.

```python
cmd = [
    "ffmpeg",
    "-i", str(video_path),
    "-vf", f"fps={fps}",          # filter to N frames/second
    str(pattern),                  # output: frame_%04d.png
    "-loglevel", "quiet",
    "-y"                           # overwrite without asking
]
```

Frames are saved to `temp_frames/<video_name>/` and deleted at the end (unless `--keep-frames` is used).

**Why ffmpeg?**
ffmpeg is the industry standard for video processing — available on all operating systems, fast and reliable.

---

## Step 2 — Frame description (Vision)

Each frame is **base64-encoded** and sent to Claude Vision in batches.

```python
content.append({
    "type": "image",
    "source": {
        "type": "base64",
        "media_type": "image/png",
        "data": encode_image(frame_path)    # base64 PNG
    }
})
```

### Why batches?

Sending frames one by one would require too many API calls. Batches (default: 10 frames) balance:

- **Quality**: Claude has context across multiple consecutive frames
- **Cost**: less overhead per call
- **Speed**: less network latency

!!! tip "When to reduce batch size?"
    With text-dense interfaces or complex UIs, reduce to `--batch-size 5`
    to give Claude more processing capacity per frame.

### Prompt sent to Vision

For each batch, Claude receives:

> *Analyze these frames in chronological order. For each frame briefly describe (1-2 sentences) what is visible: interfaces, user actions, messages, relevant elements, state changes.*

Expected format per frame:
```
Frame N (tXs): [description]
```

### Result caching

If `output/<video>_descriptions.txt` already exists, **step 2 is automatically skipped** and the existing descriptions are reused.

This allows you to:
- Resume after an interruption without extra API costs
- Regenerate only the analysis with a different prompt
- Develop and test step 3 without re-paying for Vision calls

---

## Step 3 — Process analysis

Claude receives the full frame-by-frame description text and generates a structured analysis in 5 sections.

### API parameters

```python
client.messages.stream(
    model="claude-opus-4-6",
    max_tokens=8192,
    thinking={"type": "adaptive"},      # thinks as much as needed
    output_config={"effort": "high"},   # optimizes for quality
    messages=[{"role": "user", "content": prompt}]
)
```

**Adaptive thinking**: Claude autonomously decides how much to "think" before responding. No fixed token budget — it adapts to the complexity of the task.

**Effort=high**: optimizes for output quality, not speed or cost.

**Streaming**: the analysis is printed in real time as Claude writes, avoiding timeouts on long responses.

### Report structure

```markdown
## 1. PROCESS OBJECTIVE
What is the user or system trying to accomplish? What is the expected result?

## 2. STEP-BY-STEP OPERATIONAL FLOW
For each step: action, UI element involved, result/output

## 3. IDENTIFIED TECHNICAL ELEMENTS
Systems, applications, data, visible technologies

## 4. CRITICAL OBSERVATIONS
Bottlenecks, errors, repetitive steps, attention points

## 5. OPTIMIZATION SUGGESTIONS
Concrete and specific improvements based on what was observed
```

---

## Error handling

### Interruption during step 2

If the analysis is interrupted during Vision descriptions (crash, timeout, etc.), only the descriptions from the current batch in progress are lost.

**Note**: batches are saved to the `.txt` file at the end of step 2. For more granular saving, the script can be modified to append batch by batch.

### Existing .txt file

If the descriptions file already exists, step 2 is automatically skipped. To force regeneration, delete the `.txt` file in `output/`.

---

## Design decisions

| Decision | Alternative | Reason |
|---|---|---|
| PNG frames | JPEG | PNG is lossless — better quality for text and UI |
| Batches of 10 | Single frames | Balances cost/context for Claude |
| Descriptions separate from analysis | One-shot | Enables caching, more controllable |
| Streaming for analysis | Synchronous response | Avoids timeouts, real-time feedback |
| Adaptive thinking | Fixed budget | Claude optimizes autonomously |
