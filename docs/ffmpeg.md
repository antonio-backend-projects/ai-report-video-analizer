# ffmpeg Installation and Configuration

ffmpeg is a **system tool** — it is not a Python package. It must be installed separately
and must be reachable by the script before running any analysis.

---

## How the script finds ffmpeg

The script uses a `find_ffmpeg()` function that searches in this order:

### 1. System PATH (all operating systems)

```python
shutil.which("ffmpeg")
```

If ffmpeg is in the PATH, it is used directly. **This is the normal case** on macOS and Linux.

### 2. Windows-specific paths (Windows only)

If ffmpeg is not in the PATH, the script automatically searches in the locations
where Windows package managers install it:

```python
FFMPEG_SEARCH_PATHS = [
    # WinGet (package manager included in Windows 11)
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/Packages",

    # Chocolatey
    Path("C:/ProgramData/chocolatey/bin"),

    # Scoop
    Path(os.environ.get("USERPROFILE", "")) / "scoop/apps/ffmpeg/current/bin",

    # Manual standard installation
    Path("C:/Program Files/ffmpeg/bin"),
]
```

!!! warning "These paths are Windows-only"
    On **macOS** and **Linux** the script stops at step 1 (PATH).
    If ffmpeg is not in the PATH on those systems, the script will fail.
    See the OS-specific installation instructions below.

### 3. Fallback

If ffmpeg is not found anywhere, the script returns the string `"ffmpeg"` and
on the first execution will show a clear error:

```
ERROR: ffmpeg not found. Install it from https://ffmpeg.org/download.html
```

---

## Installation by operating system

=== "Windows"

    ### Option A — WinGet *(recommended, included in Windows 11)*

    ```bash
    winget install --id Gyan.FFmpeg -e
    ```

    After installation, open a **new** terminal. WinGet installs in a subfolder of
    `%LOCALAPPDATA%\Microsoft\WinGet\Packages\` — the script finds it automatically
    with recursive search.

    ### Option B — Chocolatey

    ```bash
    choco install ffmpeg
    ```

    Installs to `C:\ProgramData\chocolatey\bin\` — detected automatically.

    ### Option C — Scoop

    ```bash
    scoop install ffmpeg
    ```

    Installs to `%USERPROFILE%\scoop\apps\ffmpeg\current\bin\` — detected automatically.

    ### Option D — Manual installation

    1. Download from [ffmpeg.org/download.html](https://ffmpeg.org/download.html) → Windows → choose a build (e.g., gyan.dev)
    2. Extract the zip
    3. Copy the extracted folder to `C:\Program Files\ffmpeg\`
    4. The structure must be:
       ```
       C:\Program Files\ffmpeg\
       └── bin\
           ├── ffmpeg.exe
           ├── ffprobe.exe
           └── ffplay.exe
       ```

    !!! tip "Adding to PATH manually"
        If you install to a different path, add the `bin\` folder to the system PATH:
        **Control Panel → System → Environment Variables → Path → Edit → New**

    ### Verify

    Open a **new** terminal (cmd or PowerShell) and type:

    ```bash
    ffmpeg -version
    ```

    Expected output (example):
    ```
    ffmpeg version 7.1 Copyright (c) 2000-2024 the FFmpeg developers
    ...
    ```

=== "macOS"

    ### With Homebrew *(recommended)*

    ```bash
    brew install ffmpeg
    ```

    Homebrew installs to `/usr/local/bin/ffmpeg` (Intel) or `/opt/homebrew/bin/ffmpeg` (Apple Silicon),
    both already in the system PATH.

    ### With MacPorts

    ```bash
    sudo port install ffmpeg
    ```

    ### Verify

    ```bash
    ffmpeg -version
    which ffmpeg   # should show the path, e.g. /opt/homebrew/bin/ffmpeg
    ```

=== "Linux (Ubuntu/Debian)"

    ### With apt

    ```bash
    sudo apt update
    sudo apt install ffmpeg
    ```

    Installs to `/usr/bin/ffmpeg` — already in PATH.

    ### Verify

    ```bash
    ffmpeg -version
    which ffmpeg   # should show /usr/bin/ffmpeg
    ```

=== "Linux (Fedora/RHEL)"

    ```bash
    sudo dnf install ffmpeg
    ```

    If the base repositories don't have ffmpeg:

    ```bash
    sudo dnf install https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm
    sudo dnf install ffmpeg
    ```

=== "Linux (Arch)"

    ```bash
    sudo pacman -S ffmpeg
    ```

---

## ffmpeg installed in a non-standard path

If you have ffmpeg installed in a custom folder and the script cannot find it,
you have two options:

### Option 1 — `FFMPEG_PATH` environment variable

Add to your `.env` file:

```env
ANTHROPIC_API_KEY=sk-ant-...
FFMPEG_PATH=C:\custom\path\ffmpeg.exe
```

Then modify the beginning of `analyze_video.py`:

```python
# Replace this line:
FFMPEG_CMD = find_ffmpeg()

# With this:
FFMPEG_CMD = os.environ.get("FFMPEG_PATH") or find_ffmpeg()
```

### Option 2 — Add the path to `FFMPEG_SEARCH_PATHS`

Edit the list directly in `analyze_video.py`:

```python
FFMPEG_SEARCH_PATHS = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/Packages",
    Path("C:/ProgramData/chocolatey/bin"),
    Path(os.environ.get("USERPROFILE", "")) / "scoop/apps/ffmpeg/current/bin",
    Path("C:/Program Files/ffmpeg/bin"),
    Path("C:/your/custom/path/bin"),  # <-- add here
]
```

### Option 3 — Add to PATH (recommended permanent solution)

Adding the ffmpeg `bin/` folder to the system PATH works on all operating systems
and is the cleanest solution. The script will find ffmpeg automatically
without any code changes.

---

## Quick diagnostics

Run this to find where ffmpeg is on your system:

=== "Windows (PowerShell)"

    ```powershell
    where.exe ffmpeg
    ```

=== "macOS / Linux"

    ```bash
    which ffmpeg
    echo $PATH
    ```

If `which ffmpeg` returns nothing, ffmpeg is not in the PATH.
