#!/usr/bin/env python3
"""
AI Video Analyzer
=================
Estrae frame dai video, li descrive con un LLM Vision (Claude o Kimi),
e genera un'analisi completa del processo mostrato.
Supporta trascrizione audio opzionale tramite Whisper (3 backend).

Utilizzo:
  python analyze_video.py                          # tutti i video in videos/
  python analyze_video.py videos/mio.mp4           # video specifico
  python analyze_video.py --fps 2                  # 2 frame al secondo
  python analyze_video.py --batch-size 5           # 5 frame per batch API
  python analyze_video.py --keep-frames            # salva screenshot in output/frames/
  python analyze_video.py --audio                  # visivo + trascrizione audio integrata
  python analyze_video.py --audio-only             # solo audio: trascrizione + analisi
  python analyze_video.py --whisper-model medium   # override modello Whisper

Variabili .env:
  LLM_PROVIDER        — anthropic | kimi (default: anthropic)
  ANTHROPIC_API_KEY   — obbligatoria se LLM_PROVIDER=anthropic
  ANTHROPIC_MODEL     — override modello (default: claude-opus-4-6)
  KIMI_API_KEY        — obbligatoria se LLM_PROVIDER=kimi
  KIMI_MODEL          — override modello (default: kimi-latest)
  KIMI_BASE_URL       — endpoint Moonshot (default: https://api.moonshot.ai/v1)
  WHISPER_BACKEND     — openai-whisper | faster-whisper | openai-api (default: faster-whisper)
  WHISPER_MODEL       — es. large-v3, medium, small, whisper-1 (default: large-v3)
  OPENAI_API_KEY      — solo se WHISPER_BACKEND=openai-api
"""

import os
import sys
import base64
import subprocess
import shutil
import argparse
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Forza UTF-8 sullo stdout per evitare errori con caratteri speciali su Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SUPPORTED_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv"}

# ─── LLM Provider config ──────────────────────────────────────────────────────

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic").lower()

ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-6")
KIMI_MODEL = os.environ.get("KIMI_MODEL", "kimi-latest")
KIMI_BASE_URL = os.environ.get("KIMI_BASE_URL", "https://api.moonshot.ai/v1")

# ─── LLM Client abstraction ───────────────────────────────────────────────────

class LLMClient:
    """Interfaccia provider-agnostica per chiamate LLM (text + vision)."""

    def vision_batch(self, items: list[dict], max_tokens: int) -> str:
        raise NotImplementedError

    def text(
        self,
        prompt: str,
        max_tokens: int,
        stream_print: bool = False,
        high_effort: bool = False,
    ) -> str:
        raise NotImplementedError


class AnthropicClient(LLMClient):
    """Claude via SDK anthropic. Usa thinking adattivo + effort alto per analisi."""

    def __init__(self):
        import anthropic  # lazy
        self._client = anthropic.Anthropic()
        self._model = ANTHROPIC_MODEL

    def _to_content(self, items):
        content = []
        for it in items:
            if it["type"] == "text":
                content.append({"type": "text", "text": it["text"]})
            elif it["type"] == "image_b64":
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": it["media_type"],
                        "data": it["data"],
                    },
                })
        return content

    def vision_batch(self, items, max_tokens):
        with self._client.messages.stream(
            model=self._model,
            max_tokens=max_tokens,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": self._to_content(items)}],
        ) as stream:
            response = stream.get_final_message()
        return "\n".join(b.text for b in response.content if b.type == "text")

    def text(self, prompt, max_tokens, stream_print=False, high_effort=False):
        kwargs = dict(
            model=self._model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        if high_effort:
            kwargs["thinking"] = {"type": "adaptive"}
            kwargs["output_config"] = {"effort": "high"}
        with self._client.messages.stream(**kwargs) as stream:
            if stream_print:
                parts = []
                for text in stream.text_stream:
                    print(text, end="", flush=True)
                    parts.append(text)
                print()
                return "".join(parts)
            response = stream.get_final_message()
            return "\n".join(b.text for b in response.content if b.type == "text")


class KimiClient(LLMClient):
    """Moonshot Kimi via SDK openai (OpenAI-compatible API)."""

    def __init__(self):
        import openai  # lazy
        api_key = os.environ.get("KIMI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "LLM_PROVIDER=kimi richiede KIMI_API_KEY nel .env"
            )
        self._client = openai.OpenAI(api_key=api_key, base_url=KIMI_BASE_URL)
        self._model = KIMI_MODEL

    def _to_content(self, items):
        content = []
        for it in items:
            if it["type"] == "text":
                content.append({"type": "text", "text": it["text"]})
            elif it["type"] == "image_b64":
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{it['media_type']};base64,{it['data']}"
                    },
                })
        return content

    def vision_batch(self, items, max_tokens):
        resp = self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": self._to_content(items)}],
        )
        return resp.choices[0].message.content or ""

    def text(self, prompt, max_tokens, stream_print=False, high_effort=False):
        # high_effort non ha equivalente diretto in Kimi: ignorato
        if stream_print:
            stream = self._client.chat.completions.create(
                model=self._model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            parts = []
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    print(delta, end="", flush=True)
                    parts.append(delta)
            print()
            return "".join(parts)
        resp = self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content or ""


def make_llm_client() -> LLMClient:
    if LLM_PROVIDER == "anthropic":
        return AnthropicClient()
    if LLM_PROVIDER == "kimi":
        return KimiClient()
    raise ValueError(
        f"LLM_PROVIDER='{LLM_PROVIDER}' non valido. Valori accettati: anthropic, kimi"
    )


# ─── Audio / Whisper config ───────────────────────────────────────────────────

WHISPER_BACKEND = os.environ.get("WHISPER_BACKEND", "faster-whisper")
# Valid values: "openai-whisper" | "faster-whisper" | "openai-api"

WHISPER_MODEL_DEFAULT = {
    "openai-whisper": "large-v3",
    "faster-whisper":  "large-v3",
    "openai-api":      "whisper-1",
}
WHISPER_MODEL = os.environ.get(
    "WHISPER_MODEL",
    WHISPER_MODEL_DEFAULT.get(WHISPER_BACKEND, "large-v3")
)

# Percorsi aggiuntivi dove cercare ffmpeg (WinGet, Chocolatey, Scoop...)
FFMPEG_SEARCH_PATHS = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/Packages",
    Path("C:/ProgramData/chocolatey/bin"),
    Path(os.environ.get("USERPROFILE", "")) / "scoop/apps/ffmpeg/current/bin",
    Path("C:/Program Files/ffmpeg/bin"),
]


def find_ffmpeg() -> str:
    """
    Cerca l'eseguibile ffmpeg nel PATH e nelle posizioni comuni di WinGet/Chocolatey/Scoop.
    Ritorna il comando/percorso da usare, oppure 'ffmpeg' se non trovato.
    """
    import shutil as _shutil
    # Prima cerca nel PATH standard
    if _shutil.which("ffmpeg"):
        return "ffmpeg"
    # Poi cerca nelle directory note
    for base in FFMPEG_SEARCH_PATHS:
        if not base.exists():
            continue
        # Cerca ricorsivamente (WinGet nidifica in sottocartelle)
        for match in base.rglob("ffmpeg.exe"):
            return str(match)
    return "ffmpeg"  # fallback: il sistema darà un errore chiaro


FFMPEG_CMD = find_ffmpeg()
_ffmpeg_path = Path(FFMPEG_CMD)
FFPROBE_CMD = str(_ffmpeg_path.parent / _ffmpeg_path.name.replace("ffmpeg", "ffprobe"))


def check_ffmpeg() -> bool:
    """Verifica che ffmpeg sia raggiungibile."""
    try:
        result = subprocess.run(
            [FFMPEG_CMD, "-version"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_video_duration(video_path: Path) -> float:
    """Ottiene la durata del video in secondi."""
    result = subprocess.run(
        [
            FFPROBE_CMD, "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path)
        ],
        capture_output=True,
        text=True
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def extract_frames(video_path: Path, output_dir: Path, fps: float = 1.0) -> list[Path]:
    """
    Estrae frame dal video usando ffmpeg.
    Ritorna la lista dei file PNG estratti.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    pattern = output_dir / "frame_%04d.png"

    cmd = [
        FFMPEG_CMD,
        "-i", str(video_path),
        "-vf", f"fps={fps}",
        str(pattern),
        "-loglevel", "quiet",
        "-y"
    ]

    print(f"  Eseguendo ffmpeg...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg ha restituito errore:\n{result.stderr}"
        )

    frames = sorted(output_dir.glob("frame_*.png"))
    print(f"  Estratti {len(frames)} frame")
    return frames


# ─── Audio extraction ─────────────────────────────────────────────────────────

def extract_audio(video_path: Path, output_path: Path) -> Path:
    """
    Estrae la traccia audio dal video come WAV mono 16 kHz PCM s16le.
    Richiesto da tutti i backend Whisper.
    Ritorna output_path.
    Solleva RuntimeError se il video non ha traccia audio.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        FFMPEG_CMD,
        "-i", str(video_path),
        "-vn",                   # no video stream
        "-acodec", "pcm_s16le",  # PCM 16-bit little-endian
        "-ar", "16000",          # 16 kHz sample rate (Whisper standard)
        "-ac", "1",              # mono
        str(output_path),
        "-loglevel", "quiet",
        "-y"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError(
            "Nessuna traccia audio trovata nel video o errore di estrazione.\n"
            "Se il video è muto, usa la pipeline senza --audio."
        )
    return output_path


# ─── Whisper transcription ────────────────────────────────────────────────────

def _transcribe_openai_whisper(audio_path: Path, model_name: str) -> str:
    """Backend: openai-whisper (locale, PyTorch)."""
    import whisper  # lazy import
    print(f"  [whisper] Carico modello '{model_name}' (openai-whisper)...")
    model = whisper.load_model(model_name)
    result = model.transcribe(str(audio_path), language=None, verbose=False)
    return result["text"].strip()


def _transcribe_faster_whisper(audio_path: Path, model_name: str) -> str:
    """Backend: faster-whisper (locale, CTranslate2)."""
    from faster_whisper import WhisperModel  # lazy import
    print(f"  [whisper] Carico modello '{model_name}' (faster-whisper)...")
    model = WhisperModel(model_name, device="auto", compute_type="default")
    segments, _ = model.transcribe(str(audio_path), language=None, beam_size=5)
    return " ".join(seg.text.strip() for seg in segments)


_OPENAI_API_LIMIT_BYTES = 25 * 1024 * 1024  # 25 MB — limite OpenAI Whisper API
_OPENAI_AUDIO_BITRATE  = "32k"             # mp3 32 kbps: ottimo per parlato, ~0.24 MB/min
_OPENAI_CHUNK_SECONDS  = 600               # 10 minuti per chunk se serve lo split


def _compress_audio_mp3(wav_path: Path) -> Path:
    """
    Converte il WAV in mp3 mono 32 kbps per ridurre le dimensioni prima dell'invio API.
    A 32 kbps il parlato è perfettamente intelligibile.
    Ritorna il percorso del file mp3 creato (stesso nome, estensione .mp3).
    """
    mp3_path = wav_path.with_suffix(".mp3")
    cmd = [
        FFMPEG_CMD,
        "-i", str(wav_path),
        "-codec:a", "libmp3lame",  # encoder mp3
        "-b:a", _OPENAI_AUDIO_BITRATE,
        "-ac", "1",                # forza mono
        str(mp3_path),
        "-loglevel", "quiet",
        "-y"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not mp3_path.exists():
        raise RuntimeError(f"Errore compressione audio mp3:\n{result.stderr}")
    return mp3_path


def _split_audio_chunks(audio_path: Path, chunk_seconds: int) -> list[Path]:
    """
    Divide un file audio in segmenti da chunk_seconds ciascuno usando ffmpeg segment.
    Ritorna la lista dei file chunk ordinati.
    """
    chunks_dir = audio_path.parent / "chunks"
    chunks_dir.mkdir(exist_ok=True)
    suffix = audio_path.suffix
    pattern = chunks_dir / f"chunk_%04d{suffix}"
    cmd = [
        FFMPEG_CMD,
        "-i", str(audio_path),
        "-f", "segment",
        "-segment_time", str(chunk_seconds),
        "-c", "copy",          # copia senza ricodificare (veloce)
        str(pattern),
        "-loglevel", "quiet",
        "-y"
    ]
    subprocess.run(cmd, capture_output=True, text=True)
    return sorted(chunks_dir.glob(f"chunk_*{suffix}"))


def _transcribe_openai_api(audio_path: Path, model_name: str) -> str:
    """
    Backend: OpenAI Whisper API (cloud).
    Pipeline:
      1. Comprimi WAV → mp3 32kbps (voce pura, ~18x più piccolo)
      2. Se mp3 < 25 MB → invio diretto
      3. Se mp3 >= 25 MB (video > ~104 min) → chunking automatico da 10 min, concatena
    """
    import openai  # lazy import
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "WHISPER_BACKEND=openai-api richiede OPENAI_API_KEY nel .env"
        )
    client = openai.OpenAI(api_key=api_key)

    # ── Step 1: comprimi in mp3 ───────────────────────────────────────────────
    print(f"  Compressione audio → mp3 {_OPENAI_AUDIO_BITRATE} (parlato)...")
    mp3_path = _compress_audio_mp3(audio_path)
    file_size_mb = mp3_path.stat().st_size / (1024 * 1024)
    print(f"  Dimensione mp3: {file_size_mb:.1f} MB")

    mp3_to_cleanup = mp3_path
    chunks_dir_to_cleanup = audio_path.parent / "chunks"

    try:
        if mp3_path.stat().st_size <= _OPENAI_API_LIMIT_BYTES:
            # ── Invio diretto ─────────────────────────────────────────────────
            with open(mp3_path, "rb") as f:
                response = client.audio.transcriptions.create(
                    model=model_name, file=f, response_format="text"
                )
            return response.strip()

        else:
            # ── Chunking automatico ───────────────────────────────────────────
            chunk_min = _OPENAI_CHUNK_SECONDS // 60
            print(
                f"  File > 25 MB: suddivisione automatica in chunk da {chunk_min} minuti..."
            )
            chunks = _split_audio_chunks(mp3_path, _OPENAI_CHUNK_SECONDS)
            print(f"  {len(chunks)} chunk da trascrivere")

            parts = []
            for i, chunk in enumerate(chunks):
                chunk_mb = chunk.stat().st_size / (1024 * 1024)
                print(f"  Chunk {i + 1}/{len(chunks)} ({chunk_mb:.1f} MB)...")
                with open(chunk, "rb") as f:
                    response = client.audio.transcriptions.create(
                        model=model_name, file=f, response_format="text"
                    )
                parts.append(response.strip())

            return " ".join(parts)

    finally:
        # Cleanup file temporanei (mp3 + chunk)
        if mp3_to_cleanup.exists():
            mp3_to_cleanup.unlink()
        if chunks_dir_to_cleanup.exists():
            shutil.rmtree(chunks_dir_to_cleanup)


def transcribe_audio(
    audio_path: Path,
    backend: str = WHISPER_BACKEND,
    model_name: str = WHISPER_MODEL,
) -> str:
    """
    Trascrive l'audio con il backend selezionato.

    Args:
        audio_path:  Percorso al file WAV (mono, 16kHz, pcm_s16le).
        backend:     "openai-whisper" | "faster-whisper" | "openai-api"
        model_name:  Dimensione/nome del modello (es. "large-v3", "whisper-1").

    Returns:
        Testo grezzo trascritto.
    """
    dispatch = {
        "openai-whisper": _transcribe_openai_whisper,
        "faster-whisper":  _transcribe_faster_whisper,
        "openai-api":      _transcribe_openai_api,
    }
    fn = dispatch.get(backend)
    if fn is None:
        raise ValueError(
            f"Backend Whisper non valido: '{backend}'. "
            f"Valori accettati: {list(dispatch)}"
        )
    print(f"  Trascrizione audio con backend '{backend}', modello '{model_name}'...")
    return fn(audio_path, model_name)


# ─── Claude Vision ────────────────────────────────────────────────────────────

def encode_image(image_path: Path) -> str:
    """Codifica un'immagine in base64."""
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def describe_frames_batch(
    client: LLMClient,
    frames: list[Path],
    batch_idx: int,
    total_batches: int,
    fps: float
) -> str:
    """
    Invia un batch di frame al LLM Vision per la descrizione.
    Ritorna il testo con le descrizioni.
    """
    items = []

    for frame_path in frames:
        # Calcola il timestamp dal numero del frame
        frame_num = int(frame_path.stem.split("_")[1])
        timestamp = (frame_num - 1) / fps

        items.append({
            "type": "text",
            "text": f"Frame {frame_num} (t={timestamp:.1f}s):"
        })
        items.append({
            "type": "image_b64",
            "media_type": "image/png",
            "data": encode_image(frame_path)
        })

    items.append({
        "type": "text",
        "text": (
            "Analizza questi frame in ordine cronologico. "
            "Per ogni frame descrivi brevemente (1-2 frasi) cosa è visibile: "
            "interfacce, azioni utente, messaggi, elementi rilevanti, cambiamenti di stato. "
            "Sii conciso e preciso. Usa questo formato esatto:\n"
            "Frame N (tXs): [descrizione]"
        )
    })

    print(f"  Batch {batch_idx + 1}/{total_batches}: {len(frames)} frame...")
    return client.vision_batch(items, max_tokens=4096)


# ─── Claude Audio ─────────────────────────────────────────────────────────────

def refine_transcript(
    client: LLMClient,
    raw_transcript: str,
    video_name: str,
) -> str:
    """
    Usa LLM per correggere il testo grezzo di Whisper:
    - Rimuove allucinazioni comuni (frasi ripetute, conclusioni inventate)
    - Aggiunge punteggiatura e paragrafi
    - NON inventa contenuto non presente nel testo
    Ritorna la trascrizione corretta.
    """
    # Guard: se la trascrizione è troppo lunga, skip refinement
    if len(raw_transcript) > 80_000:
        print(
            "  ATTENZIONE: Trascrizione molto lunga (>80k char). "
            "Raffinamento LLM saltato per evitare limiti token. "
            "La trascrizione grezza verrà salvata direttamente."
        )
        return raw_transcript

    prompt = f"""Hai ricevuto una trascrizione automatica grezza generata da Whisper per il video "{video_name}".

Il testo potrebbe contenere:
- Ripetizioni di frasi identiche ("Grazie, grazie, grazie")
- Allucinazioni tipiche di Whisper (frasi conclusive inventate tipo "Sottotitoli realizzati da...")
- Punteggiatura assente o errata
- Testo non separato in paragrafi logici

Il tuo compito:
1. Correggi SOLO errori evidenti di punteggiatura e formattazione
2. Rimuovi allucinazioni Whisper note (frasi finali tipiche, ripetizioni identiche consecutive)
3. Dividi in paragrafi dove il contesto cambia chiaramente
4. NON aggiungere, inventare o interpretare contenuto che non è presente nel testo
5. NON riassumere — restituisci il testo completo

Trascrizione grezza:
---
{raw_transcript}
---

Restituisci SOLO il testo corretto, senza spiegazioni o commenti aggiuntivi."""

    return client.text(prompt, max_tokens=8192).strip()


def analyze_audio_only(
    client: LLMClient,
    video_name: str,
    transcript: str,
    duration: float,
) -> str:
    """
    Genera summary + analisi strutturata basata SOLO sulla trascrizione audio.
    Usato con --audio-only. Streaming con output real-time.
    """
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    duration_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

    prompt = f"""Sei un esperto di analisi di processi, comunicazione e contenuti audio.

Video: **{video_name}**
Durata: {duration_str}

Qui sotto trovi la trascrizione corretta del parlato nel video:

---
{transcript}
---

Basandoti ESCLUSIVAMENTE su questa trascrizione, genera un report completo.

## 1. SOMMARIO ESECUTIVO
Riassumi in 3-5 frasi di cosa parla il video e qual è il messaggio principale.

## 2. STRUTTURA DEL CONTENUTO
Identifica le sezioni/argomenti principali nell'ordine in cui compaiono.
Per ognuna: titolo, contenuto chiave, posizione nel discorso.

## 3. ELEMENTI TECNICI E TERMINOLOGIA
- Termini tecnici, acronimi, nomi di prodotti/sistemi menzionati
- Concetti chiave spiegati o definiti nel video

## 4. AZIONI E DECISIONI IDENTIFICATE
Elenca azioni richieste all'utente, decisioni discusse, o next steps menzionati nel parlato.

## 5. OSSERVAZIONI SULLA COMUNICAZIONE
- Chiarezza e struttura del messaggio
- Punti potenzialmente ambigui o incompleti
- Suggerimenti per migliorare la comunicazione

Sii specifico e usa citazioni dirette dalla trascrizione a supporto delle osservazioni."""

    return client.text(prompt, max_tokens=8192, stream_print=True, high_effort=True)


# ─── Process Analysis ─────────────────────────────────────────────────────────

def analyze_process(
    client: LLMClient,
    video_name: str,
    descriptions: str,
    duration: float,
    transcript: str | None = None,
) -> str:
    """
    Genera un'analisi strutturata del processo dal testo delle descrizioni.
    Se transcript è presente, integra l'audio nell'analisi.
    Usa streaming e mostra l'output in tempo reale.
    """
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    duration_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

    audio_section = ""
    if transcript:
        audio_section = f"""

Trascrizione audio corretta (parlato estratto dal video):
---
{transcript}
---

Integra le informazioni audio con le osservazioni visive per un'analisi più completa e accurata.
"""

    prompt = f"""Sei un esperto di analisi di processi operativi, UX e flussi di lavoro.

Video analizzato: **{video_name}**
Durata: {duration_str}

Qui sotto trovi la trascrizione visiva cronologica del video (ogni riga descrive un frame):

---
{descriptions}
---
{audio_section}
Basandoti su queste informazioni, genera un'analisi completa e strutturata.

## 1. OBIETTIVO DEL PROCESSO
Cosa sta cercando di fare l'utente o il sistema? Qual è il risultato atteso?

## 2. FLUSSO OPERATIVO — STEP BY STEP
Elenca in ordine gli step del processo. Per ogni step indica:
- Azione compiuta
- Elemento dell'interfaccia coinvolto (se visibile)
- Risultato/output dello step

## 3. ELEMENTI TECNICI IDENTIFICATI
- Sistemi / applicazioni / interfacce utilizzate
- Dati o input coinvolti
- Tecnologie visibili

## 4. OSSERVAZIONI CRITICHE
- Colli di bottiglia o passaggi lenti
- Errori, anomalie o problemi riscontrati
- Passaggi ripetitivi o ridondanti
- Punti di attenzione per l'utente

## 5. SUGGERIMENTI DI OTTIMIZZAZIONE
Proponi miglioramenti concreti e specifici basati su quanto osservato.

Sii specifico, usa i dettagli dei frame (e dell'audio se disponibile) per supportare le osservazioni.
"""

    return client.text(prompt, max_tokens=8192, stream_print=True, high_effort=True)


# ─── Main Pipeline ────────────────────────────────────────────────────────────

def analyze_video(
    video_path: Path,
    fps: float = 1.0,
    batch_size: int = 10,
    keep_frames: bool = False,
    audio: bool = False,
    audio_only: bool = False,
    whisper_model: str | None = None,
) -> None:
    """Pipeline completa: (audio) → estrazione → descrizione → analisi."""

    client = make_llm_client()

    temp_dir = Path("temp_frames") / video_path.stem
    output_dir = Path("output")
    frames_output_dir = output_dir / "frames" / video_path.stem
    output_dir.mkdir(exist_ok=True)

    do_audio = audio or audio_only
    do_vision = not audio_only
    effective_model = whisper_model or WHISPER_MODEL

    # Step labeling
    total_steps = sum([do_audio, do_vision, do_vision, True])  # audio, frames, desc, analysis
    step = 0

    def next_step(label: str) -> str:
        nonlocal step
        step += 1
        return f"[{step}/{total_steps}] {label}"

    print(f"\n{'=' * 60}")
    print(f"  VIDEO: {video_path.name}")
    print(f"{'=' * 60}")

    duration = get_video_duration(video_path)
    if duration > 0:
        if do_vision:
            est_frames = int(duration * fps)
            print(f"  Durata: {duration:.1f}s  |  Frame stimati: {est_frames}  |  FPS: {fps}")
        else:
            print(f"  Durata: {duration:.1f}s  |  Modalità: solo audio")

    try:
        # ── Step Audio: estrazione e trascrizione ─────────────────────────────
        transcript_corrected: str | None = None

        if do_audio:
            transcript_file = output_dir / f"{video_path.stem}_trascrizione.txt"

            if transcript_file.exists():
                print(f"\n{next_step('Trascrizione già presente, riuso')} -> {transcript_file}")
                transcript_corrected = transcript_file.read_text(encoding="utf-8")
            else:
                print(f"\n{next_step('Estrazione e trascrizione audio...')}")
                temp_dir.mkdir(parents=True, exist_ok=True)
                audio_wav = temp_dir / "audio.wav"

                extract_audio(video_path, audio_wav)
                raw_transcript = transcribe_audio(
                    audio_wav,
                    backend=WHISPER_BACKEND,
                    model_name=effective_model,
                )

                print(f"  Raffinamento trascrizione con Claude...")
                transcript_corrected = refine_transcript(client, raw_transcript, video_path.name)

                transcript_file.write_text(transcript_corrected, encoding="utf-8")
                print(f"  Trascrizione salvata -> {transcript_file}")

        # ── Modalità audio-only: analisi testuale e fine ──────────────────────
        if audio_only:
            print(f"\n{next_step('Analisi audio con Claude...')}\n")
            print("-" * 60)
            audio_analysis = analyze_audio_only(
                client, video_path.name, transcript_corrected, duration
            )
            print("-" * 60)

            audio_file = output_dir / f"{video_path.stem}_audio_analisi.md"
            audio_file.write_text(
                f"# Analisi Audio: {video_path.name}\n\n{audio_analysis}",
                encoding="utf-8"
            )
            print(f"\n  Analisi audio salvata -> {audio_file}")
            return

        # ── Step 1: Estrazione frame ──────────────────────────────────────────
        print(f"\n{next_step('Estrazione frame con ffmpeg...')}")
        frames = extract_frames(video_path, temp_dir, fps)

        if not frames:
            print("  ATTENZIONE: Nessun frame estratto. Controlla che il video non sia corrotto.")
            return

        # ── Step 2: Descrizione frame (batches) ───────────────────────────────
        desc_file = output_dir / f"{video_path.stem}_descrizioni.txt"

        if desc_file.exists():
            print(f"\n{next_step('Descrizioni già presenti, riuso')} -> {desc_file}")
            descriptions_text = desc_file.read_text(encoding="utf-8")
        else:
            print(f"\n{next_step('Descrizione frame con Claude Vision...')}")
            print(f"  Totale frame: {len(frames)}  |  Batch da: {batch_size}")

            batches = [frames[i:i + batch_size] for i in range(0, len(frames), batch_size)]
            all_descriptions = []

            for i, batch in enumerate(batches):
                desc = describe_frames_batch(client, batch, i, len(batches), fps)
                all_descriptions.append(desc)

            descriptions_text = "\n\n".join(all_descriptions)
            desc_file.write_text(descriptions_text, encoding="utf-8")
            print(f"\n  Descrizioni salvate -> {desc_file}")

        # ── Step 3: Analisi del processo ──────────────────────────────────────
        print(f"\n{next_step('Analisi del processo con Claude...')}\n")
        print("-" * 60)

        analysis = analyze_process(
            client, video_path.name, descriptions_text, duration,
            transcript=transcript_corrected
        )

        print("-" * 60)

        # Salva l'analisi
        analysis_file = output_dir / f"{video_path.stem}_analisi.md"
        analysis_file.write_text(
            f"# Analisi Video: {video_path.name}\n\n{analysis}",
            encoding="utf-8"
        )
        print(f"\n  Analisi salvata -> {analysis_file}")

    finally:
        if temp_dir.exists():
            if keep_frames and do_vision:
                frames_output_dir.mkdir(parents=True, exist_ok=True)
                shutil.copytree(temp_dir, frames_output_dir, dirs_exist_ok=True)
                print(f"  Frame salvati -> {frames_output_dir}")
            shutil.rmtree(temp_dir)
            print(f"  File temporanei rimossi")


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="AI Video Analyzer — Analizza video con Claude Vision e Whisper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  python analyze_video.py                             # tutti i video in videos/
  python analyze_video.py videos/mio.mp4              # video specifico
  python analyze_video.py --fps 2                     # 2 frame/secondo (più dettaglio)
  python analyze_video.py --fps 0.5                   # 1 frame ogni 2s (più veloce)
  python analyze_video.py --batch-size 5              # batch più piccoli
  python analyze_video.py --keep-frames               # salva gli screenshot PNG
  python analyze_video.py --audio                     # visivo + trascrizione audio integrata
  python analyze_video.py --audio-only                # solo audio: trascrizione + analisi
  python analyze_video.py --audio --whisper-model medium  # override modello Whisper
        """
    )
    parser.add_argument(
        "video",
        nargs="?",
        help="Percorso del video da analizzare (default: tutti quelli in videos/)"
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=1.0,
        help="Frame al secondo da estrarre (default: 1.0)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Numero di frame per chiamata API (default: 10)"
    )
    parser.add_argument(
        "--keep-frames",
        action="store_true",
        help="Salva gli screenshot PNG in output/frames/<nome_video>/"
    )
    parser.add_argument(
        "--audio",
        action="store_true",
        help="Abilita trascrizione audio Whisper e integrazione nell'analisi"
    )
    parser.add_argument(
        "--audio-only",
        action="store_true",
        help="Salta la pipeline visiva: trascrive solo l'audio e genera analisi testuale"
    )
    parser.add_argument(
        "--whisper-model",
        type=str,
        default=None,
        metavar="MODEL",
        help=(
            f"Override del modello Whisper (default: WHISPER_MODEL dal .env = '{WHISPER_MODEL}'). "
            "Esempi: large-v3, medium, small, whisper-1"
        )
    )

    args = parser.parse_args()

    # --audio-only implica --audio
    if args.audio_only:
        args.audio = True

    # Controllo API key in base al provider
    if LLM_PROVIDER == "anthropic":
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("ERRORE: LLM_PROVIDER=anthropic richiede ANTHROPIC_API_KEY nel .env.")
            print("Copia .env.example in .env e inserisci la tua API key.")
            sys.exit(1)
    elif LLM_PROVIDER == "kimi":
        if not os.environ.get("KIMI_API_KEY"):
            print("ERRORE: LLM_PROVIDER=kimi richiede KIMI_API_KEY nel .env.")
            print("Copia .env.example in .env e inserisci la tua API key Kimi.")
            sys.exit(1)
    else:
        print(f"ERRORE: LLM_PROVIDER='{LLM_PROVIDER}' non valido. Valori accettati: anthropic, kimi")
        sys.exit(1)

    # Controllo ffmpeg
    if not check_ffmpeg():
        print("ERRORE: ffmpeg non trovato. Installalo da https://ffmpeg.org/download.html")
        sys.exit(1)

    # Validazione fps
    if args.fps <= 0 or args.fps > 30:
        print("ERRORE: --fps deve essere tra 0.1 e 30")
        sys.exit(1)

    # Validazione backend Whisper (solo se audio richiesto)
    valid_backends = {"openai-whisper", "faster-whisper", "openai-api"}
    if args.audio:
        if WHISPER_BACKEND not in valid_backends:
            print(
                f"ERRORE: WHISPER_BACKEND='{WHISPER_BACKEND}' non valido. "
                f"Valori accettati: {', '.join(sorted(valid_backends))}"
            )
            sys.exit(1)
        if WHISPER_BACKEND == "openai-api" and not os.environ.get("OPENAI_API_KEY"):
            print("ERRORE: WHISPER_BACKEND=openai-api richiede OPENAI_API_KEY nel .env")
            sys.exit(1)

    # Kwargs comuni
    video_kwargs = dict(
        fps=args.fps,
        batch_size=args.batch_size,
        keep_frames=args.keep_frames,
        audio=args.audio,
        audio_only=args.audio_only,
        whisper_model=args.whisper_model,
    )

    if args.video:
        # Video specifico
        video_path = Path(args.video)
        if not video_path.exists():
            print(f"ERRORE: File non trovato: {video_path}")
            sys.exit(1)
        if video_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            print(f"ERRORE: Formato non supportato. Usa: {', '.join(SUPPORTED_EXTENSIONS)}")
            sys.exit(1)

        analyze_video(video_path, **video_kwargs)

    else:
        # Tutti i video in videos/
        videos_dir = Path("videos")
        if not videos_dir.exists():
            print("ERRORE: Cartella 'videos/' non trovata nella directory corrente.")
            sys.exit(1)

        videos = [
            p for p in sorted(videos_dir.iterdir())
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

        if not videos:
            print(f"Nessun video trovato in {videos_dir}/")
            print(f"Formati supportati: {', '.join(SUPPORTED_EXTENSIONS)}")
            sys.exit(1)

        print(f"Trovati {len(videos)} video da analizzare:")
        for v in videos:
            print(f"  - {v.name}")

        for video in videos:
            analyze_video(video, **video_kwargs)

        print(f"\n{'=' * 60}")
        print(f"  COMPLETATO — Output salvato in output/")
        print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
