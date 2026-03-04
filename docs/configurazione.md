# Configuration

All configurable options for the tool.

---

## Environment variables

Configured in the `.env` file at the project root.

### `ANTHROPIC_API_KEY` *(required)*

Your Anthropic API key.

```env
ANTHROPIC_API_KEY=sk-ant-api03-...
```

!!! danger "Do not commit .env"
    The `.env` file is already excluded by `.gitignore`. Never hardcode the key
    directly in source code.

---

### `WHISPER_BACKEND` *(optional — needed only with --audio / --audio-only)*

Selects the audio transcription backend.

```env
WHISPER_BACKEND=faster-whisper
```

| Value | Description | Requires |
|---|---|---|
| `faster-whisper` | Local, CTranslate2 — fast, lightweight | `pip install faster-whisper` |
| `openai-whisper` | Local, PyTorch — official OpenAI library | `pip install openai-whisper` |
| `openai-api` | Cloud — OpenAI Whisper API | `pip install openai` + `OPENAI_API_KEY` |

**Default:** `faster-whisper`

See [Audio Transcription](audio.md) for a full backend comparison.

---

### `WHISPER_MODEL` *(optional)*

Model size for local backends, or model name for `openai-api`.

```env
WHISPER_MODEL=large-v3
```

| Value | Backend | Size | Quality |
|---|---|---|---|
| `tiny` | local | ~39 MB | Basic |
| `base` | local | ~74 MB | Good |
| `small` | local | ~244 MB | Better |
| `medium` | local | ~769 MB | High |
| `large-v3` | local | ~1.5 GB | Best |
| `whisper-1` | openai-api | cloud | High |

**Default:** `large-v3` (local backends), `whisper-1` (openai-api)

Can be overridden at runtime with `--whisper-model`.

---

### `OPENAI_API_KEY` *(optional — only for openai-api backend)*

Your OpenAI API key. Required only when `WHISPER_BACKEND=openai-api`.

```env
OPENAI_API_KEY=sk-...
```

Obtain from [platform.openai.com/api-keys](https://platform.openai.com/api-keys).

---

## CLI parameters

All parameters are passed on the command line at runtime.

---

### `--fps`

**Type**: float
**Default**: `1.0`
**Valid range**: `0.1` — `30`

Frames extracted per second from the video. Controls how many "snapshots" are analyzed.

```bash
python analyze_video.py --fps 1.0   # default: 1 frame/second
python analyze_video.py --fps 2     # 2 frames/second (more detail)
python analyze_video.py --fps 0.5   # 1 frame every 2 seconds (faster)
```

#### Guidelines

| Video type | Recommended FPS | Reason |
|---|---|---|
| Software tutorials, UX flows | `1.0` | Actions are slow and visible |
| Fast processes with many actions | `2.0` | Captures quick actions |
| Long videos (>10 min) | `0.5` | Reduces costs and processing time |
| Demos with fast animations | `3.0` | Avoids missing transitions |

!!! warning "Impact on cost"
    Doubling the FPS doubles the frames, API calls, and cost.
    For a 5-minute video: fps=1 → 300 frames, fps=2 → 600 frames.

---

### `--batch-size`

**Type**: int
**Default**: `10`
**Valid range**: `1` — `50`

Number of frames sent in a single call to Claude Vision.

```bash
python analyze_video.py --batch-size 10   # default
python analyze_video.py --batch-size 5    # smaller batches
python analyze_video.py --batch-size 20   # larger batches
```

#### When to change it

| Situation | Recommended batch |
|---|---|
| Text-dense UI (forms, tables, code) | `5` |
| Video with many simple screens | `15-20` |
| Token limit errors from API | Reduce to `5` |
| Fewer API calls desired | Increase to `20` |

!!! info "Tokens per image"
    Each PNG frame uses approximately 1000-3000 tokens depending on visual complexity.
    With `batch-size=10`, each Vision call uses ~20,000 input tokens.

---

### `--keep-frames`

**Type**: flag (boolean)
**Default**: disabled

Saves all extracted PNG screenshots to `output/frames/<video_name>/`.

```bash
python analyze_video.py --keep-frames
```

**Without** `--keep-frames` (default): temporary frames are deleted at the end.

**With** `--keep-frames`: frames are copied to `output/frames/` before the temp directory is removed.

#### When to use it

- To visually verify the frames Claude analyzed
- For debugging if the analysis seems inaccurate
- To keep screenshots as visual process documentation
- For presentations accompanying the text report

---

## Advanced configuration

### Changing the model

The model is defined at the top of `analyze_video.py`:

```python
MODEL = "claude-opus-4-6"
```

Available models:

| Model | Quality | Speed | Cost |
|---|---|---|---|
| `claude-opus-4-6` | ★★★ | Slow | High |
| `claude-sonnet-4-6` | ★★☆ | Medium | Medium |
| `claude-haiku-4-5` | ★☆☆ | Fast | Low |

!!! tip "Sonnet for the Vision step"
    You can use Sonnet for step 2 (frame descriptions) and Opus for step 3 (final analysis),
    reducing costs without sacrificing report quality.

### Customizing the analysis prompt

The step 3 prompt is in the `analyze_process()` function in `analyze_video.py`.
You can customize it to adapt to your domain (e.g., security analysis, compliance, training).

### Folder paths

Configurable directly in `analyze_video.py`:

```python
temp_dir = Path("temp_frames") / video_path.stem     # temporary frames
output_dir = Path("output")                           # final output
frames_output_dir = output_dir / "frames" / video_path.stem  # saved frames
```
