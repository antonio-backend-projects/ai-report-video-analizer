#!/usr/bin/env python3
"""
AI Video Analyzer
=================
Estrae frame dai video, li descrive con Claude Vision (claude-opus-4-6),
e genera un'analisi completa del processo mostrato.

Utilizzo:
  python analyze_video.py                    # analizza tutti i video in videos/
  python analyze_video.py videos/mio.mp4    # analizza un video specifico
  python analyze_video.py --fps 2           # 2 frame al secondo
  python analyze_video.py --batch-size 5   # 5 frame per batch API
  python analyze_video.py --keep-frames    # salva gli screenshot in output/frames/
"""

import os
import sys
import base64
import subprocess
import shutil
import argparse
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

# Forza UTF-8 sullo stdout per evitare errori con caratteri speciali su Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MODEL = "claude-opus-4-6"
SUPPORTED_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv"}

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


# ─── Claude Vision ────────────────────────────────────────────────────────────

def encode_image(image_path: Path) -> str:
    """Codifica un'immagine in base64."""
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def describe_frames_batch(
    client: anthropic.Anthropic,
    frames: list[Path],
    batch_idx: int,
    total_batches: int,
    fps: float
) -> str:
    """
    Invia un batch di frame a Claude Vision per la descrizione.
    Ritorna il testo con le descrizioni.
    """
    content = []

    for frame_path in frames:
        # Calcola il timestamp dal numero del frame
        frame_num = int(frame_path.stem.split("_")[1])
        timestamp = (frame_num - 1) / fps

        content.append({
            "type": "text",
            "text": f"Frame {frame_num} (t={timestamp:.1f}s):"
        })
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": encode_image(frame_path)
            }
        })

    content.append({
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

    with client.messages.stream(
        model=MODEL,
        max_tokens=4096,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": content}]
    ) as stream:
        response = stream.get_final_message()

    text_parts = [b.text for b in response.content if b.type == "text"]
    return "\n".join(text_parts)


# ─── Process Analysis ─────────────────────────────────────────────────────────

def analyze_process(
    client: anthropic.Anthropic,
    video_name: str,
    descriptions: str,
    duration: float
) -> str:
    """
    Genera un'analisi strutturata del processo dal testo delle descrizioni.
    Usa streaming e mostra l'output in tempo reale.
    """
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    duration_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

    prompt = f"""Sei un esperto di analisi di processi operativi, UX e flussi di lavoro.

Video analizzato: **{video_name}**
Durata: {duration_str}

Qui sotto trovi la trascrizione visiva cronologica del video (ogni riga descrive un frame):

---
{descriptions}
---

Basandoti ESCLUSIVAMENTE su queste descrizioni, genera un'analisi completa e strutturata.

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

Sii specifico, usa i dettagli dei frame per supportare le osservazioni.
"""

    result_parts = []

    with client.messages.stream(
        model=MODEL,
        max_tokens=8192,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            result_parts.append(text)

    print()
    return "".join(result_parts)


# ─── Main Pipeline ────────────────────────────────────────────────────────────

def analyze_video(
    video_path: Path,
    fps: float = 1.0,
    batch_size: int = 10,
    keep_frames: bool = False
) -> None:
    """Pipeline completa: estrazione ->descrizione ->analisi."""

    client = anthropic.Anthropic()

    temp_dir = Path("temp_frames") / video_path.stem
    output_dir = Path("output")
    frames_output_dir = output_dir / "frames" / video_path.stem
    output_dir.mkdir(exist_ok=True)

    print(f"\n{'=' * 60}")
    print(f"  VIDEO: {video_path.name}")
    print(f"{'=' * 60}")

    duration = get_video_duration(video_path)
    if duration > 0:
        est_frames = int(duration * fps)
        print(f"  Durata: {duration:.1f}s  |  Frame stimati: {est_frames}  |  FPS: {fps}")

    try:
        # ── Step 1: Estrazione frame ──────────────────────────────────────────
        print(f"\n[1/3] Estrazione frame con ffmpeg...")
        frames = extract_frames(video_path, temp_dir, fps)

        if not frames:
            print("  ATTENZIONE: Nessun frame estratto. Controlla che il video non sia corrotto.")
            return

        # ── Step 2: Descrizione frame (batches) ───────────────────────────────
        desc_file = output_dir / f"{video_path.stem}_descrizioni.txt"

        if desc_file.exists():
            print(f"\n[2/3] Descrizioni gia' presenti, riuso -> {desc_file}")
            descriptions_text = desc_file.read_text(encoding="utf-8")
        else:
            print(f"\n[2/3] Descrizione frame con Claude Vision...")
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
        print(f"\n[3/3] Analisi del processo con Claude...\n")
        print("-" * 60)

        analysis = analyze_process(client, video_path.name, descriptions_text, duration)

        print("-" * 60)

        # Salva l'analisi
        analysis_file = output_dir / f"{video_path.stem}_analisi.md"
        full_report = f"# Analisi Video: {video_path.name}\n\n{analysis}"
        analysis_file.write_text(full_report, encoding="utf-8")
        print(f"\n  Analisi salvata ->{analysis_file}")

    finally:
        if temp_dir.exists():
            if keep_frames:
                frames_output_dir.mkdir(parents=True, exist_ok=True)
                shutil.copytree(temp_dir, frames_output_dir, dirs_exist_ok=True)
                print(f"  Frame salvati ->{frames_output_dir}")
            shutil.rmtree(temp_dir)
            print(f"  Frame temporanei rimossi")


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="AI Video Analyzer — Analizza video con Claude Vision",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  python analyze_video.py                         # tutti i video in videos/
  python analyze_video.py videos/mio.mp4          # video specifico
  python analyze_video.py --fps 2                 # 2 frame/secondo (più dettaglio)
  python analyze_video.py --fps 0.5               # 1 frame ogni 2s (più veloce)
  python analyze_video.py --batch-size 5          # batch più piccoli
  python analyze_video.py --keep-frames           # salva gli screenshot PNG
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

    args = parser.parse_args()

    # Controllo API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERRORE: Variabile d'ambiente ANTHROPIC_API_KEY non trovata.")
        print("Copia .env.example in .env e inserisci la tua API key.")
        sys.exit(1)

    # Controllo ffmpeg
    if not check_ffmpeg():
        print("ERRORE: ffmpeg non trovato. Installalo da https://ffmpeg.org/download.html")
        sys.exit(1)

    # Validazione fps
    if args.fps <= 0 or args.fps > 30:
        print("ERRORE: --fps deve essere tra 0.1 e 30")
        sys.exit(1)

    if args.video:
        # Video specifico
        video_path = Path(args.video)
        if not video_path.exists():
            print(f"ERRORE: File non trovato: {video_path}")
            sys.exit(1)
        if video_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            print(f"ERRORE: Formato non supportato. Usa: {', '.join(SUPPORTED_EXTENSIONS)}")
            sys.exit(1)

        analyze_video(video_path, args.fps, args.batch_size, args.keep_frames)

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
            analyze_video(video, args.fps, args.batch_size, args.keep_frames)

        print(f"\n{'=' * 60}")
        print(f"  COMPLETATO — Output salvato in output/")
        print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
