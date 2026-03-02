# AI Video Analyzer

Strumento Python che analizza video muti usando **Claude Vision** (claude-opus-4-6) e genera automaticamente un report strutturato del processo mostrato.

---

## Come funziona

```
VIDEO.mp4
   │
   ▼
[ffmpeg] estrae 1 frame/secondo
   │
   ▼
[Claude Vision] descrive ogni frame (cosa vede, interfacce, azioni)
   │
   ▼
[Claude Opus] analizza l'intero flusso e genera il report
   │
   ▼
output/
 ├── video_descrizioni.txt   ← trascrizione visiva frame-by-frame
 └── video_analisi.md        ← report strutturato del processo
```

---

## Cosa produce

Dando in input un video che registra un'operazione (tutorial software, flusso UX, processo aziendale...), ottieni:

- **Descrizioni frame-by-frame** — cosa appare in ogni secondo del video
- **Report di analisi** con:
    - Obiettivo del processo
    - Flusso step-by-step
    - Elementi tecnici identificati
    - Osservazioni e colli di bottiglia
    - Suggerimenti di ottimizzazione

---

## Quick Start

```bash
# 1. Installa dipendenze
pip install -r requirements.txt

# 2. Configura API key
cp .env.example .env
# modifica .env con la tua ANTHROPIC_API_KEY

# 3. Metti i video in videos/

# 4. Lancia
python analyze_video.py
```

Risultati in `output/`.

---

## Tecnologie

| Componente | Tecnologia |
|---|---|
| Estrazione frame | ffmpeg |
| Vision AI | Claude Opus 4.6 (Vision) |
| Analisi processo | Claude Opus 4.6 |
| SDK | anthropic (Python) |
