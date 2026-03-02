# Installazione

## Requisiti

- Python 3.10+
- ffmpeg installato nel sistema
- API key Anthropic

---

## 1. ffmpeg

ffmpeg è un tool di sistema, va installato separatamente da Python.

=== "Windows"

    ```bash
    # Con winget (incluso in Windows 11)
    winget install ffmpeg

    # Con Chocolatey
    choco install ffmpeg

    # Con Scoop
    scoop install ffmpeg
    ```

    Dopo l'installazione apri un **nuovo** terminale e verifica:

    ```bash
    ffmpeg -version
    ```

=== "macOS"

    ```bash
    brew install ffmpeg
    ```

=== "Linux (Ubuntu/Debian)"

    ```bash
    sudo apt update && sudo apt install ffmpeg
    ```

---

## 2. Dipendenze Python

```bash
pip install -r requirements.txt
```

Il file `requirements.txt` installa:

| Package | Uso |
|---|---|
| `anthropic` | Client per Claude API (Vision + analisi) |
| `python-dotenv` | Lettura API key da file `.env` |
| `mkdocs-material` | Questa documentazione |

---

## 3. API Key Anthropic

1. Vai su [console.anthropic.com](https://console.anthropic.com)
2. Crea una API key
3. Copia `.env.example` in `.env`:

    ```bash
    cp .env.example .env
    ```

4. Incolla la tua chiave nel file `.env`:

    ```
    ANTHROPIC_API_KEY=sk-ant-...
    ```

!!! warning "Non committare il file .env"
    Il file `.env` contiene la tua chiave privata. Non aggiungerlo mai a git.

---

## 4. Verifica installazione

```bash
python analyze_video.py --help
```

Output atteso:

```
usage: analyze_video.py [-h] [--fps FPS] [--batch-size BATCH_SIZE] [--keep-frames] [video]

AI Video Analyzer — Analizza video con Claude Vision
...
```

---

## Struttura cartelle

```
ai-video-analizer/
├── videos/           ← metti qui i tuoi video
├── output/           ← risultati (creata automaticamente)
│   ├── frames/       ← screenshot PNG (solo con --keep-frames)
│   ├── *_descrizioni.txt
│   └── *_analisi.md
├── docs/             ← questa documentazione
├── analyze_video.py
├── requirements.txt
├── mkdocs.yml
└── .env              ← la tua API key (non committare!)
```
