# Installation

## Requirements

- Python 3.10+
- ffmpeg installed on the system
- Anthropic API key

---

## 1. ffmpeg

ffmpeg is a system tool — it must be installed separately from Python.

=== "Windows"

    ```bash
    # With winget (included in Windows 11)
    winget install ffmpeg

    # With Chocolatey
    choco install ffmpeg

    # With Scoop
    scoop install ffmpeg
    ```

    After installation, open a **new** terminal and verify:

    ```bash
    ffmpeg -version
    ```

    !!! info "ffmpeg not found after installation?"
        See the [ffmpeg configuration](ffmpeg.md) page for details on how the script
        searches for ffmpeg on Windows and how to handle non-standard install paths.

=== "macOS"

    ```bash
    brew install ffmpeg
    ```

=== "Linux (Ubuntu/Debian)"

    ```bash
    sudo apt update && sudo apt install ffmpeg
    ```

---

## 2. Python dependencies

```bash
pip install -r requirements.txt
```

The `requirements.txt` installs the core packages:

| Package | Purpose |
|---|---|
| `anthropic` | Claude API client (Vision + analysis) |
| `python-dotenv` | Read API key from `.env` file |
| `mkdocs-material` | This documentation (optional) |

---

## 3. Whisper backend *(optional — for --audio / --audio-only)*

Install **one** of the three backends depending on your needs:

=== "faster-whisper (Recommended)"

    Local, fast, no PyTorch needed.

    ```bash
    pip install faster-whisper
    ```

    Then in `.env`:
    ```
    WHISPER_BACKEND=faster-whisper
    WHISPER_MODEL=large-v3
    ```

=== "openai-whisper (Official)"

    Local, official OpenAI library. Requires PyTorch (~2 GB download).

    ```bash
    pip install openai-whisper
    ```

    Then in `.env`:
    ```
    WHISPER_BACKEND=openai-whisper
    WHISPER_MODEL=large-v3
    ```

=== "openai-api (Cloud)"

    No local installation. Calls OpenAI Whisper API. Requires an OpenAI API key.

    ```bash
    pip install openai
    ```

    Then in `.env`:
    ```
    WHISPER_BACKEND=openai-api
    WHISPER_MODEL=whisper-1
    OPENAI_API_KEY=sk-...
    ```

!!! info "No backend installed?"
    The script runs normally without any Whisper package. Audio flags are simply not available
    until a backend is installed and configured.

---

## 4. Anthropic API key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create an API key
3. Copy `.env.example` to `.env`:

    ```bash
    cp .env.example .env
    ```

4. Paste your key into `.env`:

    ```
    ANTHROPIC_API_KEY=sk-ant-...
    ```

!!! warning "Do not commit .env"
    The `.env` file contains your private key. Never add it to git.
    It is already excluded by `.gitignore`.

---

## 5. Verify installation

```bash
python analyze_video.py --help
```

Expected output:

```
usage: analyze_video.py [-h] [--fps FPS] [--batch-size BATCH_SIZE] [--keep-frames] [video]

AI Video Analyzer — Analyze videos with Claude Vision
...
```

---

## Folder structure

```
ai-report-video-analizer/
├── videos/                    ← place your videos here
├── output/                    ← results (created automatically)
│   ├── frames/                ← PNG screenshots (only with --keep-frames)
│   ├── *_descrizioni.txt      ← frame-by-frame visual transcript
│   ├── *_analisi.md           ← structured process report
│   ├── *_trascrizione.txt     ← audio transcript (with --audio)
│   └── *_audio_analisi.md     ← audio-only report (with --audio-only)
├── docs/                      ← this documentation
├── analyze_video.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── mkdocs.yml
└── .env                       ← your API keys (do not commit!)
```
