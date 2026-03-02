# API Costs

Estimated Anthropic costs for using the tool.

---

## Claude Opus 4.6 pricing

| Token type | Price |
|---|---|
| Input | $5.00 / 1M tokens |
| Output | $25.00 / 1M tokens |

*Prices as of March 2026. Check [anthropic.com/pricing](https://anthropic.com/pricing) for updates.*

---

## Cost per step

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

The analysis call uses the description text as input.

**Estimate:**

| Item | Average tokens |
|---|---|
| Prompt + descriptions | ~N_frames × 50 input |
| Generated report | ~3,000 output |

---

## Cost table by video

| Video length | FPS | Frames | Step 2 | Step 3 | **Total** |
|---|---|---|---|---|---|
| 2 minutes | 1 | 120 | ~$0.13 | ~$0.09 | ~**$0.22** |
| 5 minutes | 1 | 300 | ~$0.33 | ~$0.10 | ~**$0.43** |
| 5 minutes | 2 | 600 | ~$0.66 | ~$0.11 | ~**$0.77** |
| 10 minutes | 1 | 600 | ~$0.66 | ~$0.11 | ~**$0.77** |
| 10 minutes | 2 | 1,200 | ~$1.32 | ~$0.12 | ~**$1.44** |
| 20 minutes | 1 | 1,200 | ~$1.32 | ~$0.12 | ~**$1.44** |
| 20 minutes | 0.5 | 600 | ~$0.66 | ~$0.11 | ~**$0.77** |

!!! note "Approximate values"
    Actual tokens vary based on the visual density of frames (an interface
    with lots of text costs more than a nearly empty screen).

---

## Strategies to reduce costs

### 1. Lower the FPS

```bash
python analyze_video.py --fps 0.5   # halves the number of frames
```

Use `0.5` for long videos or with slow actions (e.g., system waits, static screens).

### 2. Increase batch-size

```bash
python analyze_video.py --batch-size 20
```

Reduces the number of API calls (less overhead), but does not change total token count.

### 3. Reuse descriptions

If you only need to change the analysis prompt, **do not delete** the `_descriptions.txt` file.
Step 2 (Vision, the most expensive) will be automatically skipped.

### 4. Use Sonnet for descriptions

Modify `MODEL` in `analyze_video.py` or use two different models:
- **Sonnet** for step 2 (frame descriptions): sufficient quality, ~40% lower cost
- **Opus** for step 3 (analysis): maximum quality where it matters

### 5. Test on short clips

Before processing a long video, test with a 2-3 minute sample to verify
the quality meets expectations.

---

## Cost monitoring

From the Anthropic dashboard:

- [console.anthropic.com/usage](https://console.anthropic.com/usage) — token usage by date
- [console.anthropic.com/settings/limits](https://console.anthropic.com/settings/limits) — set a monthly spending limit

!!! tip "Set a spending limit"
    In the Anthropic Console you can configure a **monthly budget** that blocks
    requests when the limit is reached. Useful for development environments.
