# Troubleshooting

Solutions to the most common issues.

---

## ffmpeg not found

### Error

```
ERROR: ffmpeg not found. Install it from https://ffmpeg.org/download.html
```

or:

```
FileNotFoundError: [WinError 2] The system cannot find the file specified
```

### Cause

ffmpeg is not in the system PATH.

### Solution

=== "Windows — WinGet"

    ```bash
    winget install ffmpeg
    ```

    Open a **new** terminal after installation. The script also searches for ffmpeg
    in `%LOCALAPPDATA%\Microsoft\WinGet\Packages\` automatically.

=== "Windows — Chocolatey"

    ```bash
    choco install ffmpeg
    ```

=== "macOS"

    ```bash
    brew install ffmpeg
    ```

=== "Linux"

    ```bash
    sudo apt update && sudo apt install ffmpeg
    ```

**Verify:**

```bash
ffmpeg -version
```

See the [ffmpeg configuration](ffmpeg.md) page for details on non-standard install paths.

---

## Encoding error — Windows

### Error

```
UnicodeEncodeError: 'charmap' codec can't encode character '\u2192'
```

### Cause

The Windows terminal uses codepage cp1252 instead of UTF-8. Claude generates characters
like `→`, `—`, `€` that cp1252 does not support.

### Solution

Start Python with the UTF-8 flag:

```bash
python -X utf8 analyze_video.py
```

Or set it permanently in the terminal:

```bash
# PowerShell
$env:PYTHONUTF8 = "1"
python analyze_video.py

# Command Prompt
set PYTHONUTF8=1
python analyze_video.py
```

---

## Invalid API key

### Error

```
ERROR: ANTHROPIC_API_KEY environment variable not found.
```

or a 401 error from the API.

### Solution

1. Verify the `.env` file exists at the project root
2. Verify it contains the key in the correct format:

```
ANTHROPIC_API_KEY=sk-ant-api03-...
```

3. No spaces around the `=`
4. The key must start with `sk-ant-`

---

## No frames extracted

### Error

```
WARNING: No frames extracted. Check that the video is not corrupted.
```

### Causes and solutions

**Corrupted video**: try opening the video with a player (VLC).

**Unsupported format**: verify the extension is one of `.mp4`, `.avi`, `.mkv`, `.mov`, `.webm`, `.flv`.

**Path with special characters**: if the path contains spaces or special characters, use quotes:

```bash
python analyze_video.py "videos/video with spaces.mp4"
```

---

## Error during Vision batch

### Error

```
anthropic.BadRequestError: ...
```

or truncated response from Claude Vision.

### Cause

The batch has too many tokens (frames are too heavy or batch-size is too high).

### Solution

Reduce the batch-size:

```bash
python analyze_video.py --batch-size 5
```

---

## Incomplete or inaccurate analysis

### Symptom

The final report is vague, lacks detail, or describes things that do not match the video.

### Causes and solutions

**FPS too low**: some actions are not captured.

```bash
python analyze_video.py --fps 2
```

**Batches too large**: Claude receives too many frames per call and cannot describe them all accurately.

```bash
python analyze_video.py --batch-size 5
```

**Check the descriptions**: look at the `_descrizioni.txt` file to see if the individual frame-by-frame descriptions are accurate. If they are but the final analysis is poor, the problem is in step 3.

**Regenerate only the analysis**: if the descriptions are correct, you can regenerate only the analysis without re-paying for Vision — the `_descrizioni.txt` file will be reused automatically.

---

## Process interrupted midway

### Symptom

The script stops during step 2 (frame description).

### Solution

Relaunch the script with the same parameters. If the `_descrizioni.txt` file exists partially, delete it and relaunch:

```bash
# Delete partial descriptions
del output\video_descrizioni.txt   # Windows
rm output/video_descrizioni.txt    # macOS/Linux

# Relaunch
python analyze_video.py videos/video.mp4
```

---

## `videos/` folder not found

### Error

```
ERROR: 'videos/' folder not found in the current directory.
```

### Solution

Create the folder manually:

```bash
mkdir videos
```

Or specify the video path directly:

```bash
python analyze_video.py /full/path/to/video.mp4
```

---

## Anthropic rate limit

### Error

```
anthropic.RateLimitError: ...
```

### Cause

Too many requests in a short time (requests-per-minute limit).

### Solution

The Anthropic SDK automatically handles retries with exponential backoff.
If the issue persists, reduce the number of videos processed in parallel.

For free or basic tier accounts, consider increasing `--batch-size` to
make fewer total calls:

```bash
python analyze_video.py --batch-size 15
```

---

## "Nessuna traccia audio trovata nel video"

### Error

```
RuntimeError: Nessuna traccia audio trovata nel video o errore di estrazione.
Se il video è muto, usa la pipeline senza --audio.
```

### Cause

The video has no audio stream (screen recording without microphone), or ffmpeg could not extract it.

### Solution

Remove `--audio` or `--audio-only` from the command:

```bash
python analyze_video.py videos/mute_screen_recording.mp4
```

To verify if a video has audio:
```bash
ffprobe -i videos/mio.mp4 2>&1 | grep Audio
```

If no output appears, the video has no audio track.

---

## "WHISPER_BACKEND non valido"

### Error

```
ERRORE: WHISPER_BACKEND='xyz' non valido. Valori accettati: faster-whisper, openai-whisper, openai-api
```

### Solution

Check `.env` and set one of the valid values:

```env
WHISPER_BACKEND=faster-whisper
```

---

## "OPENAI_API_KEY non trovata"

### Error

```
ERRORE: WHISPER_BACKEND=openai-api richiede OPENAI_API_KEY nel .env
```

### Solution

Add your OpenAI key to `.env`:

```env
OPENAI_API_KEY=sk-...
```

Obtain from [platform.openai.com/api-keys](https://platform.openai.com/api-keys).

---

## Whisper package not installed

### Error

```
ModuleNotFoundError: No module named 'faster_whisper'
```

or:

```
ModuleNotFoundError: No module named 'whisper'
```

### Solution

Install the backend matching your `WHISPER_BACKEND` setting:

```bash
# faster-whisper
pip install faster-whisper

# openai-whisper
pip install openai-whisper

# openai-api
pip install openai
```

---

## Whisper transcription is slow

### Symptom

Transcription takes a very long time (tens of minutes for a short video).

### Causes and solutions

**Large model on CPU**: `large-v3` on CPU is slow. Use a smaller model:

```bash
python analyze_video.py --audio --whisper-model medium
python analyze_video.py --audio --whisper-model base   # fastest
```

**Use the cloud API** instead of local transcription:

```env
# .env
WHISPER_BACKEND=openai-api
WHISPER_MODEL=whisper-1
OPENAI_API_KEY=sk-...
```

---

## Poor transcription quality

### Symptom

The transcript contains errors, repeated phrases, or garbled text.

### Causes and solutions

**Use a larger model**:
```bash
python analyze_video.py --audio --whisper-model large-v3
```

**Audio quality**: low-quality microphone or background noise reduces accuracy for all Whisper backends.

**Claude refinement**: the transcript refinement step (always active) already corrects common Whisper hallucinations. If the raw transcript is very poor, Claude may not be able to fully recover it.

**Try a different backend**: `openai-whisper` and `faster-whisper` can produce slightly different results on the same audio — try both if quality is an issue.

---

## mp3 compression fails (openai-api backend)

### Error

```
RuntimeError: Errore compressione audio mp3:
```

### Cause

The `libmp3lame` encoder is missing from the ffmpeg build.

### Solution

Install a full ffmpeg build that includes mp3 encoding:

```bash
# Windows
winget install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

Verify mp3 support:
```bash
ffmpeg -codecs 2>/dev/null | grep mp3
```

You should see `libmp3lame` in the output.
