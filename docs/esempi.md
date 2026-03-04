# Real Examples

Examples of analyses performed on real process and meeting videos.

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

## Example 3 — Team meeting (audio-only)

**Video**: `riunione-2026-03-01.mp4`
**Duration**: ~45 minutes
**Mode**: `--audio-only` (no Vision API)
**Whisper backend**: `openai-api`

### Command used

```bash
python analyze_video.py videos/riunione-2026-03-01.mp4 --audio-only
```

### Runtime output

```
[1/2] Estrazione e trascrizione audio...
  Compressione audio → mp3 32k (parlato)...
  Dimensione mp3: 6.4 MB
  Trascrizione audio con backend 'openai-api', modello 'whisper-1'...
  Raffinamento trascrizione con Claude...
  Trascrizione salvata -> output/riunione-2026-03-01_trascrizione.txt

[2/2] Analisi audio con Claude...
```

### Excerpt from the generated audio analysis

```markdown
## 1. SOMMARIO ESECUTIVO
La riunione riguarda la pianificazione del rilascio della versione 3.0 del software
gestionale. Il team discute le priorità delle funzionalità rimanenti, i tempi di
consegna e la distribuzione del carico di lavoro tra i team frontend e backend.
Il messaggio principale è che il rilascio è confermato per il 15 aprile, con
possibilità di slittamento di una settimana per il modulo di reportistica.

## 4. AZIONI E DECISIONI IDENTIFICATE
- Mario completa il modulo di autenticazione entro venerdì
- Sara prepara i test di regressione per lunedì prossimo
- Il team si riunisce giovedì per il review finale della roadmap
- La funzionalità di export PDF viene rimossa dalla v3.0 e spostata alla v3.1
```

---

## Example 4 — TED Talk with visual + audio (included sample)

**Video**: `ted_clint_smith.mp4` *(included in `videos/` — ready to run)*
**Duration**: ~262 seconds
**Extracted frames**: 263 (fps=1)
**Mode**: `--audio` (visual + Whisper transcription integrated)
**Whisper backend**: `faster-whisper`, model `base`

### Command used

```bash
python analyze_video.py videos/ted_clint_smith.mp4 --audio --whisper-model base
```

### Runtime output

```
============================================================
  VIDEO: ted_clint_smith.mp4
============================================================
  Durata: 262.6s  |  Frame stimati: 262  |  FPS: 1.0

[1/4] Estrazione e trascrizione audio...
  Trascrizione audio con backend 'faster-whisper', modello 'base'...
  [whisper] Carico modello 'base' (faster-whisper)...
  Raffinamento trascrizione con Claude...
  Trascrizione salvata -> output/ted_clint_smith_trascrizione.txt

[2/4] Estrazione frame con ffmpeg...
  Estratti 263 frame

[3/4] Descrizione frame con Claude Vision...
  Totale frame: 263  |  Batch da: 10
  Batch 1/27: 10 frame...
  [...]
  Batch 27/27: 3 frame...
  Descrizioni salvate -> output/ted_clint_smith_descrizioni.txt

[4/4] Analisi del processo con Claude...
  Analisi salvata -> output/ted_clint_smith_analisi.md
```

### Corrected transcript (`_trascrizione.txt`)

```
Dr. Martin Luther King, Jr., in a 1968 speech where he reflects upon the civil
rights movement, states, "In the end, we will remember not the words of our
enemies, but the silence of our friends."

As a teacher, I've internalized this message. Every day, all around us, we see
the consequences of silence manifest themselves in the form of discrimination,
violence, genocide, and war. [...]

Silence is the residue of fear. It is feeling your flaws gut-wrench, guillotine
your tongue. It is the air retreating from your chest because it doesn't feel
safe in your lungs. Silence is Rwandan genocide. Silence is Katrina. [...]

So this year, instead of giving something up, I will live every day as if there
were a microphone tucked under my tongue, a stage on the underside of my
inhibition. Because who has to have a soapbox when all you've ever needed is
your voice?
```

*Zero hallucinations. Poetic lines and proper nouns correctly captured by model `base`.*

### Excerpt from the generated report (`_analisi.md`)

```markdown
## 1. PROCESS OBJECTIVE

Clint Smith intends to **persuade the audience to break their silence in the face
of injustice**, using the TED Talk as a vehicle for spoken-word poetry blended
with autobiographical narrative.

| Level | Expected outcome |
|---|---|
| **Cognitive** | Audience internalizes the thesis: "silence is the residue of fear" |
| **Emotional** | Visceral response through concrete images (Christian beaten, the homeless man) |
| **Behavioral** | Push to action: speak, tell your truth |

## 4. CRITICAL OBSERVATIONS

- **Rhetorical structure**: chiastic mirror structure (A-B-C-X-C'-B'-A') — every
  second is functional; 3 silence cases in the narrative are rewritten as 3 acts
  of speech in the resolution
- **Gesture as parallel sign system**: hands in pockets = silence/vulnerability;
  open palms upward = offering/question; fist raised = determination — all
  synchronized frame-by-frame with the spoken text
- **Deliberate final pause**: Smith stops with ~2 minutes still on the timer.
  Six seconds of chosen silence after a talk against passive silence — the most
  elegant example of form matching content in the entire piece
- **Production note**: 12-second branded intro (4.6% of total runtime) risks
  viewer drop-off before Smith speaks; the MLK quote would be a stronger cold open
```

---

## Typical use cases

### UX flow analysis

```bash
python analyze_video.py videos/user-session.mp4 --fps 2
```

Every user interaction documented with timestamp, UI element involved, visible result.

---

### Narrated tutorial (visual + audio)

```bash
python analyze_video.py videos/software-tutorial.mp4 --fps 1 --audio
```

Step-by-step process report enriched with the spoken explanations from the narrator.

---

### Meeting / webinar transcription

```bash
python analyze_video.py videos/webinar.mp4 --audio-only
```

Clean transcript + structured summary with key topics, decisions, and action items.

---

### Business process audit

```bash
python analyze_video.py videos/operational-workflow.mp4 --fps 1 --batch-size 5
```

Analysis focusing on bottlenecks and optimization suggestions.

---

### Long video (>15 min)

```bash
python analyze_video.py videos/long.mp4 --fps 0.5 --batch-size 15
```

Reduces frames and API calls to keep costs down for very long videos.

---

### Long meeting with audio

```bash
python analyze_video.py videos/long-meeting.mp4 --audio-only --whisper-model large-v3
```

For recordings over 1 hour, the audio is automatically compressed and chunked if needed.
No manual intervention required.

---

## FPS comparison on the same video

| fps | Frames | Estimated cost | Analysis quality |
|---|---|---|---|
| 0.5 | 160 | ~$0.22 | General overview |
| 1.0 | 320 | ~$0.43 | **Optimal for most cases** |
| 2.0 | 640 | ~$0.77 | Useful for fast processes |

*Indicative values for a ~320-second video, visual only.*
