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
| `--batch-size` | `10` | Frames sent per API call |
| `--keep-frames` | off | Save PNG screenshots to `output/frames/` |

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
  ├── frame_0003.png   (t=2s)
  └── ...
```

Useful to visually verify which frames were analyzed.

---

## Combined examples

```bash
# Specific video, 2fps, with saved screenshots
python analyze_video.py videos/tutorial.mp4 --fps 2 --keep-frames

# All videos, fast analysis (0.5fps)
python analyze_video.py --fps 0.5

# Long video with small batches for more accuracy
python analyze_video.py videos/long.mp4 --fps 1 --batch-size 5 --keep-frames
```

---

## Runtime output

```
============================================================
  VIDEO: tutorial.mp4
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
  Descriptions saved -> output/tutorial_descriptions.txt

[3/3] Analyzing process with Claude...

------------------------------------------------------------
## 1. PROCESS OBJECTIVE
...
------------------------------------------------------------

  Analysis saved -> output/tutorial_analysis.md
  Frames saved -> output/frames/tutorial
  Temporary frames removed
```
