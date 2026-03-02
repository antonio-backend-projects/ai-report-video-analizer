# Utilizzo

## Comandi principali

### Analizza tutti i video in `videos/`

```bash
python analyze_video.py
```

Processa in sequenza tutti i file `.mp4 .avi .mkv .mov .webm .flv` trovati nella cartella `videos/`.

---

### Analizza un video specifico

```bash
python analyze_video.py videos/mio_video.mp4
```

---

## Opzioni

| Opzione | Default | Descrizione |
|---|---|---|
| `--fps` | `1.0` | Frame estratti al secondo |
| `--batch-size` | `10` | Frame inviati per ogni chiamata API |
| `--keep-frames` | off | Salva gli screenshot PNG in `output/frames/` |

---

### `--fps` — dettaglio dell'analisi

Controlla quanti frame al secondo vengono estratti dal video.

```bash
# 1 frame al secondo (default, buono per la maggior parte dei casi)
python analyze_video.py --fps 1

# 2 frame al secondo (più dettaglio, più lento e costoso)
python analyze_video.py --fps 2

# 1 frame ogni 2 secondi (più veloce, meno dettaglio)
python analyze_video.py --fps 0.5
```

!!! tip "Quanti fps usare?"
    - **Tutorial software / flussi UX**: 1 fps è perfetto
    - **Processi veloci con molte azioni**: usa 2 fps
    - **Video lunghi (>10 min)**: usa 0.5 fps per risparmiare

---

### `--batch-size` — dimensione batch

Quanti frame vengono inviati in una singola chiamata API a Claude Vision.

```bash
# Batch da 5 frame (usa meno token per chiamata)
python analyze_video.py --batch-size 5

# Batch da 20 frame (meno chiamate API, ma più token per chiamata)
python analyze_video.py --batch-size 20
```

!!! info "Quando ridurre il batch?"
    Se il video ha frame molto densi di informazioni (testo piccolo, UI complessa),
    riduci il batch a 5 per dare più "spazio" a Claude per analizzare ogni frame.

---

### `--keep-frames` — salva gli screenshot

```bash
python analyze_video.py --keep-frames
```

Salva tutti gli screenshot PNG estratti dal video in:
```
output/frames/<nome_video>/
  ├── frame_0001.png   (t=0s)
  ├── frame_0002.png   (t=1s)
  ├── frame_0003.png   (t=2s)
  └── ...
```

Utile per verificare visivamente quali frame sono stati analizzati.

---

## Esempi combinati

```bash
# Video specifico, 2fps, con screenshot salvati
python analyze_video.py videos/tutorial.mp4 --fps 2 --keep-frames

# Tutti i video, analisi veloce (0.5fps)
python analyze_video.py --fps 0.5

# Video lungo con batch piccoli per più accuratezza
python analyze_video.py videos/lungo.mp4 --fps 1 --batch-size 5 --keep-frames
```

---

## Output durante l'esecuzione

```
============================================================
  VIDEO: tutorial.mp4
============================================================
  Durata: 245.3s  |  Frame stimati: 245  |  FPS: 1.0

[1/3] Estrazione frame con ffmpeg...
  Eseguendo ffmpeg...
  Estratti 245 frame

[2/3] Descrizione frame con Claude Vision...
  Totale frame: 245  |  Batch da: 10
  Batch 1/25: 10 frame...
  Batch 2/25: 10 frame...
  ...
  Descrizioni salvate → output/tutorial_descrizioni.txt

[3/3] Analisi del processo con Claude...

------------------------------------------------------------
## 1. OBIETTIVO DEL PROCESSO
...
------------------------------------------------------------

  Analisi salvata → output/tutorial_analisi.md
  Frame salvati → output/frames/tutorial
  Frame temporanei rimossi
```
