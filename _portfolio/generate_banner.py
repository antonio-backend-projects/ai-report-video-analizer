"""Generate the 1280x720 portfolio banner for ai-report-video-analyzer."""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1280, 720
OUT = os.path.join(os.path.dirname(__file__), "ai-report-video-analyzer.png")

FONT_DIR = "C:/Windows/Fonts/"

def font(name, size):
    for candidate in [name, name.lower(), name.replace("b.ttf", ".ttf")]:
        try:
            return ImageFont.truetype(FONT_DIR + candidate, size)
        except Exception:
            pass
    return ImageFont.load_default()

f_title  = font("calibrib.ttf", 52)
f_sub    = font("calibri.ttf",  26)
f_label  = font("calibrib.ttf", 17)
f_small  = font("calibri.ttf",  15)
f_tag    = font("calibri.ttf",  14)
f_badge  = font("calibrib.ttf", 13)

# ── Colors ──────────────────────────────────────────────────────────────────────
BG       = (10,  14,  20)
BG2      = (16,  22,  30)
ACCENT   = (224, 123,  84)
PURPLE   = (130,  80, 220)
GREEN    = ( 63, 185,  80)
BLUE     = ( 88, 166, 255)
WHITE    = (240, 246, 252)
MUTED    = (130, 148, 158)
DARK_BOX = ( 22,  30,  40)
BORDER   = ( 35,  48,  60)

img = Image.new("RGB", (W, H), BG)
d   = ImageDraw.Draw(img)

# background grid
for x in range(0, W, 60):
    d.line([(x, 0), (x, H)], fill=(18, 26, 36), width=1)
for y in range(0, H, 60):
    d.line([(0, y), (W, y)], fill=(18, 26, 36), width=1)

# top accent bar + left stripe
d.rectangle([(0, 0), (W, 4)], fill=ACCENT)
d.rectangle([(0, 4), (4, H)], fill=(30, 42, 56))

# ── Title block ─────────────────────────────────────────────────────────────────
d.rectangle([(60, 44), (820, 155)], fill=(16, 22, 30), outline=(35, 48, 60), width=1)
d.rectangle([(60, 44), (63, 155)], fill=ACCENT)
d.text((76, 52),  "PORTFOLIO PROJECT",                                          font=f_tag,   fill=ACCENT)
d.text((76, 72),  "AI Report Video Analyzer",                                   font=f_title, fill=WHITE)
d.text((76, 132), "Claude Vision + Whisper  ->  structured process reports, automated", font=f_sub, fill=MUTED)

# ── Pipeline nodes ──────────────────────────────────────────────────────────────
NODES = [
    {"label": "1  VIDEO INPUT",   "sub": ".mp4  .avi  .mkv\n.mov  .webm  .flv",  "col": (40, 55, 72),  "border": (60, 90, 110), "tx": WHITE},
    {"label": "2  ffmpeg",        "sub": "Frame extraction\n1 PNG / second",       "col": (20, 50, 30),  "border": GREEN,         "tx": GREEN},
    {"label": "3  Claude Vision", "sub": "Batch description\nAdaptive thinking",   "col": (50, 30, 20),  "border": ACCENT,        "tx": ACCENT},
    {"label": "4  Whisper AI",    "sub": "Audio transcript\n3 backends",            "col": (35, 20, 60),  "border": PURPLE,        "tx": PURPLE},
    {"label": "5  REPORT",        "sub": "_analisi.md\n_trascrizione.txt",          "col": (20, 40, 60),  "border": BLUE,          "tx": BLUE},
]

NODE_W  = 194
NODE_H  = 110
START_X = 60
GAP     = 28
TOP_Y   = 195
ARROW_Y = TOP_Y + NODE_H // 2

for i, n in enumerate(NODES):
    x0 = START_X + i * (NODE_W + GAP)
    x1 = x0 + NODE_W
    y0 = TOP_Y
    y1 = y0 + NODE_H

    d.rectangle([(x0+4, y0+4), (x1+4, y1+4)], fill=(6, 10, 16))
    d.rectangle([(x0, y0), (x1, y1)], fill=n["col"], outline=n["border"], width=2)
    d.ellipse([(x0+10, y0+10), (x0+30, y0+30)], fill=n["border"])
    d.text((x0+12, y0+12), n["label"], font=f_label, fill=n["tx"])

    for j, line in enumerate(n["sub"].split("\n")):
        d.text((x0+12, y0+46 + j*20), line, font=f_small, fill=WHITE)

    if i < len(NODES) - 1:
        ax0 = x1 + 2
        ax1 = x1 + GAP - 2
        ay  = ARROW_Y
        d.line([(ax0, ay), (ax1-8, ay)], fill=BORDER, width=2)
        d.polygon([(ax1-8, ay-5), (ax1, ay), (ax1-8, ay+5)], fill=BORDER)

# ── Mode badges ─────────────────────────────────────────────────────────────────
MODES = [
    ("DEFAULT  --  visual only",     "3 steps   |   1 fps   |   ~$0.43 / 5 min",  ACCENT),
    ("--audio  --  visual + speech", "4 steps   |   Whisper + Vision",              PURPLE),
    ("--audio-only  --  transcript", "2 steps   |   zero Vision API cost",          BLUE),
]
MODE_Y = 330
for i, (title, detail, col) in enumerate(MODES):
    bx = 60 + i * 408
    bw, bh = 390, 68
    d.rectangle([(bx, MODE_Y), (bx+bw, MODE_Y+bh)], fill=DARK_BOX, outline=col, width=1)
    d.rectangle([(bx, MODE_Y), (bx+3, MODE_Y+bh)], fill=col)
    d.text((bx+14, MODE_Y+10), title,  font=f_badge, fill=col)
    d.text((bx+14, MODE_Y+34), detail, font=f_small, fill=MUTED)

# ── Tech stack pills ────────────────────────────────────────────────────────────
TECHS = [
    ("Python 3.11",    (55, 118, 171)),
    ("Claude Opus 4.6", ACCENT),
    ("faster-whisper",  PURPLE),
    ("ffmpeg",          GREEN),
    ("Docker",          (29, 99, 237)),
    ("MkDocs Material", (72, 175, 240)),
    ("openai-whisper",  (116, 191, 67)),
    ("OpenAI API",      (103, 194, 170)),
]
TECH_Y = 432
tx = 60
for tech, col in TECHS:
    tw = int(d.textlength(tech, font=f_small)) + 22
    d.rounded_rectangle([(tx, TECH_Y), (tx+tw, TECH_Y+26)], radius=4, fill=(22, 32, 44), outline=col, width=1)
    d.text((tx+11, TECH_Y+5), tech, font=f_small, fill=col)
    tx += tw + 10

# ── Terminal output box ─────────────────────────────────────────────────────────
BOX_X, BOX_Y, BOX_W, BOX_H = 60, 490, 760, 195
d.rectangle([(BOX_X, BOX_Y), (BOX_X+BOX_W, BOX_Y+BOX_H)], fill=(8, 12, 18), outline=BORDER, width=1)
d.rectangle([(BOX_X, BOX_Y), (BOX_X+BOX_W, BOX_Y+26)], fill=(22, 30, 40))
d.ellipse([(BOX_X+10, BOX_Y+8),  (BOX_X+22, BOX_Y+20)], fill=(255,  95,  86))
d.ellipse([(BOX_X+28, BOX_Y+8),  (BOX_X+40, BOX_Y+20)], fill=(255, 189,  46))
d.ellipse([(BOX_X+46, BOX_Y+8),  (BOX_X+58, BOX_Y+20)], fill=( 39, 201,  63))
d.text((BOX_X+BOX_W//2 - 120, BOX_Y+6), "output / ted_clint_smith_analisi.md", font=f_small, fill=MUTED)

terminal_lines = [
    ("$ python analyze_video.py videos/ted_clint_smith.mp4 --audio --whisper-model base", GREEN),
    ("[1/4] Estrazione e trascrizione audio...                                           ", MUTED),
    ("  Trascrizione salvata -> output/ted_clint_smith_trascrizione.txt                 ", WHITE),
    ("[3/4] Descrizione frame con Claude Vision... 27 batch / 263 frame                 ", MUTED),
    ("[4/4] Analisi del processo con Claude...                                           ", MUTED),
    ("  ## 1. OBIETTIVO  -- Persuadere a rompere il silenzio (Clint Smith TED)          ", ACCENT),
    ("  Struttura retorica A-B-C-X-C-B-A identificata. Pausa finale: scelta deliberata  ", WHITE),
    ("  Analisi salvata -> output/ted_clint_smith_analisi.md                            ", GREEN),
]
for i, (line, col) in enumerate(terminal_lines):
    d.text((BOX_X+14, BOX_Y+34 + i*19), line[:95], font=f_small, fill=col)

# ── Stats panel ─────────────────────────────────────────────────────────────────
PANEL_X, PANEL_Y, PANEL_W, PANEL_H = 846, 490, 374, 195
d.rectangle([(PANEL_X, PANEL_Y), (PANEL_X+PANEL_W, PANEL_Y+PANEL_H)], fill=DARK_BOX, outline=BORDER, width=1)
stats = [
    ("~700",   "lines of code (single file)",     ACCENT),
    ("3",      "Whisper backends supported",        PURPLE),
    ("5",      "report sections generated",         BLUE),
    ("~$0.51", "per 5-min video (visual+audio)",   GREEN),
    ("inf",    "video duration (auto-chunking)",    WHITE),
]
d.text((PANEL_X+16, PANEL_Y+12), "AT A GLANCE", font=f_badge, fill=MUTED)
for i, (val, label, col) in enumerate(stats):
    sy = PANEL_Y + 40 + i*30
    d.text((PANEL_X+16, sy),    val,   font=f_label, fill=col)
    d.text((PANEL_X+80, sy+2),  label, font=f_small, fill=MUTED)

# ── Bottom bar ──────────────────────────────────────────────────────────────────
d.rectangle([(0, H-36), (W, H)], fill=(14, 20, 28))
d.rectangle([(0, H-36), (W, H-35)], fill=BORDER)
d.text((70,  H-24), "github.com/antoniotrento/ai-report-video-analizer", font=f_small, fill=MUTED)
d.text((880, H-24), "antoniotrento.net  -  2026", font=f_small, fill=MUTED)

img.save(OUT, "PNG", optimize=True)
print(f"Saved: {OUT}  ({W}x{H})")
