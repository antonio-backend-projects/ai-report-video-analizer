# Real Examples

Examples of analyses performed on real CRM process videos.

---

## Example 1 — Electricity connection (PN1)

**Video**: `PN1-2026-02-20 11-45-38.mp4`
**Duration**: ~320 seconds
**Extracted frames**: 320 (fps=1)
**System analyzed**: CRM NET@SIU (Metamer)

### Command used

```bash
python analyze_video.py "videos/PN1-2026-02-20 11-45-38.mp4" --keep-frames
```

### Excerpt from the generated report

```markdown
## 1. PROCESS OBJECTIVE
The user is managing an electricity grid connection request for a residential
customer in the NET@SIU CRM system. The goal is to complete the registration
of the connection request, entering customer data, technical installation
characteristics, and initiating the bureaucratic process for the connection.

## 2. STEP-BY-STEP OPERATIONAL FLOW

1. **Opening the case**
   - Action: opening case code 2026/1024001
   - Interface: NET@SIU dashboard
   - Result: customer FERRANTE ANTONELLA record displayed

2. **Address verification**
   - Action: checking personal data and installation location
   - Interface: Customer Registry section
   - Result: address VIA PESCARA 58 - SAN FELICE DEL MOLISE (CB) confirmed

[... 60+ steps analyzed ...]

## 4. CRITICAL OBSERVATIONS
- High loading times between screens (3-5 seconds per page)
- Repetitive technical data entry compared to already present data
- No autocomplete for cadastral codes
- Field validation only on save, not in real time
```

---

## Example 2 — Gas connection (E01)

**Video**: `E01-2026-02-20 11-51-01.mp4`
**Duration**: ~246 seconds
**Extracted frames**: 246 (fps=1)
**System analyzed**: CRM NET@SIU (Metamer)

### Command used

```bash
python analyze_video.py "videos/E01-2026-02-20 11-51-01.mp4" --keep-frames
```

### Process characteristics identified

The report identified:

- **System**: NET@SIU CRM (Metamer) — web interface
- **Case type**: E01 — Residential gas connection
- **Customer**: same registry as PN1 video
- **Case code**: 2026/1024005
- **Total steps**: ~40 distinct operations
- **Main bottleneck**: double cadastral verification with system wait

---

## Typical use cases

### UX flow analysis

```bash
python analyze_video.py videos/user-session.mp4 --fps 2
```

You get: every user interaction documented with timestamp, UI element involved, visible result.

### Tutorial documentation

```bash
python analyze_video.py videos/software-tutorial.mp4 --fps 1 --keep-frames
```

You get: step-by-step tutorial with a screenshot for each step.

### Business process audit

```bash
python analyze_video.py videos/operational-workflow.mp4 --fps 1 --batch-size 5
```

You get: analysis focusing on bottlenecks and optimization suggestions.

### Long video (>15 min)

```bash
python analyze_video.py videos/long.mp4 --fps 0.5 --batch-size 15
```

Reduces frames and API calls to keep costs down for very long videos.

---

## FPS comparison on the same video

| fps | Frames | Estimated cost | Analysis quality |
|---|---|---|---|
| 0.5 | 160 | ~$0.22 | General overview |
| 1.0 | 320 | ~$0.43 | **Optimal for most cases** |
| 2.0 | 640 | ~$0.77 | Useful for fast processes |

*Indicative values for a ~320-second video.*
