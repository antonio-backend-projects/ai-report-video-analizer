---
title: "AI Report Video Analyzer"
subtitle: "Pipeline multimodale Claude Vision + Whisper per generare report strutturati da registrazioni video"
date: 2026-03-04
tags: [Python, Claude API, Whisper, ffmpeg, Docker, AI, Vision, NLP]
github: https://github.com/antoniotrento/ai-report-video-analizer
status: released
---

# AI Report Video Analyzer

> Un tool Python single-file che trasforma automaticamente registrazioni video — screencast aziendali, tutorial, riunioni — in report strutturati pronti per la documentazione, l'audit di processo o la knowledge base, usando Claude Vision e Whisper AI.

---

## Il problema che risolve

Chiunque lavori con video operativi conosce il collo di bottiglia: c'è una registrazione di 10 minuti che mostra come un operatore lavora su un gestionale, oppure una riunione di un'ora in cui sono state prese decisioni importanti, oppure un tutorial che bisogna documentare per il manuale utente. Guardare quei video richiede tempo reale — non si può andare a 2x senza perdere dettagli. Prendere appunti mentre si guarda è inefficiente. Affidarsi alla memoria è inaffidabile.

Il problema non è la mancanza di contenuto: è la **frizione tra il contenuto video e il testo strutturato** che le organizzazioni effettivamente usano — nei documenti, nei ticket, nelle basi di conoscenza, nelle analisi di processo.

Ho lavorato per mesi con questo tipo di video nel contesto dell'analisi di processi operativi su sistemi CRM aziendali. Ogni sessione richiedeva ore di revisione manuale per produrre un documento di analisi decente. La domanda che mi sono posto era semplice: può un modello AI multimodale fare questo lavoro in modo autonomo, con una qualità accettabile per uso professionale?

La risposta, dopo aver costruito e testato questo tool, è sì.

---

## Cosa produce il tool

Dato un file video, il tool genera automaticamente:

- **`video_descrizioni.txt`** — trascrizione visiva frame-per-frame: per ogni secondo del video, una descrizione dell'interfaccia, dell'azione dell'utente, dei messaggi visibili, dei cambiamenti di stato
- **`video_analisi.md`** — report strutturato in 5 sezioni: obiettivo del processo, flusso operativo step-by-step, elementi tecnici identificati, osservazioni critiche, suggerimenti di ottimizzazione
- **`video_trascrizione.txt`** — (con `--audio`) trascrizione corretta del parlato, ripulita dalle allucinazioni di Whisper
- **`video_audio_analisi.md`** — (con `--audio-only`) sommario esecutivo, struttura del contenuto, azioni e decisioni identificate

Tutto questo da un singolo comando:

```bash
python analyze_video.py videos/sessione.mp4 --audio
```

---

## Architettura della pipeline

Il progetto è volutamente un **single-file Python** (`analyze_video.py`, ~700 righe). Non una libreria, non un'applicazione web: uno script che fa una cosa sola ma la fa bene, con tre modalità operative che si selezionano via CLI.

### Modalità 1 — Solo visivo (default)

La pipeline di base è in tre step:

**Step 1 — Estrazione frame con ffmpeg**

ffmpeg viene invocato via subprocess per estrarre frame PNG dal video alla frequenza configurata (default: 1 fps). I frame vengono salvati temporaneamente in `temp_frames/` e rimossi alla fine, a meno che non si usi `--keep-frames`.

```python
cmd = [
    FFMPEG_CMD,
    "-i", str(video_path),
    "-vf", f"fps={fps}",     # filtro frequenza frame
    str(pattern),            # output: frame_%04d.png
    "-loglevel", "quiet",
    "-y"
]
```

La scelta di PNG invece di JPEG è deliberata: PNG è lossless, e per interfacce con testo (menu, form, tabelle) la qualità dell'encoding fa differenza nella capacità di lettura del modello Vision.

**Step 2 — Descrizione frame con Claude Vision (batch)**

I frame vengono base64-encoded e inviati a Claude Vision in batch (default: 10 per chiamata). Ogni batch include i frame come immagini inline nella request API, con un prompt che chiede descrizioni ordinate temporalmente in formato strutturato:

```
Frame N (tXs): [descrizione]
```

Il batching bilancia qualità (Claude ha contesto su più frame consecutivi), costo (meno overhead per chiamata) e velocità (meno latenza di rete). Per interfacce dense di testo o UI complesse, `--batch-size 5` migliora la precisione.

**Caching automatico**: se `output/video_descrizioni.txt` esiste già, lo step 2 viene saltato. Questo permette di rigenerare l'analisi con prompt diversi, o di riprendere dopo un'interruzione, senza ripa-gare per le chiamate Vision.

**Step 3 — Analisi di processo con Claude Opus (adaptive thinking)**

L'intero testo di descrizioni viene inviato a Claude Opus per la generazione del report finale. Qui la scelta tecnica più rilevante è l'uso di `thinking={"type": "adaptive"}` con `output_config={"effort": "high"}`:

```python
client.messages.stream(
    model="claude-opus-4-6",
    max_tokens=8192,
    thinking={"type": "adaptive"},
    output_config={"effort": "high"},
    messages=[{"role": "user", "content": prompt}]
)
```

Il thinking adattivo permette al modello di decidere autonomamente quanta elaborazione interna dedicare alla risposta, in funzione della complessità del task. L'effort "high" sposta il tradeoff verso la qualità dell'output. Entrambi vengono applicati solo nello step finale di analisi — non nel raffinamento della trascrizione, dove il task è editoriale e non richiede ragionamento profondo.

L'output viene stampato in streaming real-time per evitare timeout su analisi lunghe e dare feedback visivo all'utente durante l'attesa.

---

### Modalità 2 — Visivo + Audio (`--audio`)

Aggiunge un primo step (step 1 su 4) di estrazione e trascrizione audio prima della pipeline visiva. La trascrizione corretta viene poi integrata nel prompt dello step di analisi finale, dando al modello sia il contesto visivo che quello parlato.

La pipeline completa diventa:

```
[1/4] Audio extraction → Whisper transcription → Claude refinement
[2/4] Frame extraction (ffmpeg)
[3/4] Frame description (Claude Vision, batch)
[4/4] Process analysis (Claude Opus, visual + transcript integrated)
```

L'integrazione audio/visivo nello step 4 non è una semplice concatenazione: il prompt specifica esplicitamente che il modello ha accesso sia alle descrizioni visive frame-per-frame che alla trascrizione del parlato, e che deve usarle entrambe per costruire un'analisi coerente che correli gesti, azioni sullo schermo e parole pronunciate.

---

### Modalità 3 — Solo audio (`--audio-only`)

Salta completamente la pipeline visiva. Nessuna estrazione frame, nessuna chiamata Vision. Utile per riunioni, webinar, tutorial vocali in cui il parlato contiene più informazione dello schermo.

```
[1/2] Audio extraction → Whisper → Claude refinement
[2/2] Claude audio analysis (summary + struttura + osservazioni)
```

Il report generato in questa modalità ha una struttura diversa: sommario esecutivo, struttura del contenuto, terminologia tecnica, azioni/decisioni identificate, osservazioni sulla comunicazione.

---

## Il sistema di trascrizione audio

Questa è stata la parte più complessa da progettare. L'obiettivo era supportare tre backend completamente diversi con una singola interfaccia, gestire il limite di file dell'API OpenAI, e non crashare se il pacchetto di un backend non era installato.

### Tre backend, un dispatcher

```python
def transcribe_audio(audio_path: Path, backend: str, model_name: str) -> str:
    fn = {
        "openai-whisper": _transcribe_openai_whisper,
        "faster-whisper":  _transcribe_faster_whisper,
        "openai-api":      _transcribe_openai_api,
    }.get(backend)
    if fn is None:
        raise ValueError(f"WHISPER_BACKEND='{backend}' non valido.")
    return fn(audio_path, model_name)
```

Ogni backend usa **lazy import**: l'`import whisper` (o `from faster_whisper import WhisperModel`, o `import openai`) avviene solo al momento della chiamata, non all'avvio dello script. Questo significa che il tool funziona correttamente anche se nessuno dei pacchetti Whisper è installato — semplicemente, se si usa `--audio` senza il backend configurato, si ottiene un `ModuleNotFoundError` chiaro invece di un crash all'avvio.

**faster-whisper** è il backend consigliato per uso locale. È basato su CTranslate2 invece di PyTorch, il che lo rende ~4x più veloce e con un footprint di memoria significativamente inferiore. Non richiede CUDA per funzionare ma ne beneficia se disponibile (`device="auto"`).

**openai-whisper** è il backend ufficiale OpenAI, basato su PyTorch. Più lento, immagine Docker più grande (~4-5 GB vs ~1.5 GB), ma in alcuni casi produce risultati leggermente diversi che possono essere utili confrontare.

**openai-api** usa le API cloud di OpenAI. Zero installazione locale, qualità alta, ma ha il limite di 25 MB per file. Da qui il problema più interessante da risolvere.

### Il problema dei 25 MB: compressione e chunking automatico

Un WAV mono 16 kHz (il formato che Whisper preferisce) pesa circa 1.875 MB al minuto. Una riunione di un'ora fa ~112 MB — quasi 5 volte il limite. Ma per la trascrizione vocale, la qualità audio rilevante è solo quella della voce umana, non la fedeltà audiofila.

La soluzione è in due livelli:

**Livello 1 — Compressione mp3 32 kbps**

WAV viene convertito in mp3 mono a 32 kbps usando il codec `libmp3lame` via ffmpeg:

```python
def _compress_audio_mp3(wav_path: Path) -> Path:
    cmd = [
        FFMPEG_CMD,
        "-i", str(wav_path),
        "-codec:a", "libmp3lame",
        "-b:a", "32k",   # 32 kbps: ~0.24 MB/min, ottimo per parlato
        "-ac", "1",      # forza mono
        str(mp3_path),
        ...
    ]
```

A 32 kbps il parlato è perfettamente intelligibile — è il bitrate dei podcast low-quality, sufficiente per Whisper che lavora su segnale già elaborato. Il fattore di compressione è ~18x: da 1.875 MB/min a ~0.24 MB/min. Il limite di 25 MB diventa ~104 minuti di parlato continuo.

**Livello 2 — Chunking automatico per video >104 min**

Se dopo la compressione il file è ancora sopra i 25 MB, scatta il chunking automatico con ffmpeg `segment`:

```python
def _split_audio_chunks(audio_path: Path, chunk_seconds: int) -> list[Path]:
    cmd = [
        FFMPEG_CMD,
        "-i", str(audio_path),
        "-f", "segment",
        "-segment_time", str(chunk_seconds),  # 600s = 10 min
        "-c", "copy",     # copia senza ricodificare (veloce)
        str(pattern),
        ...
    ]
```

Ogni chunk viene trascritto separatamente e i testi vengono concatenati. Il cleanup dei file temporanei avviene in un blocco `finally` per garantire la pulizia anche in caso di errore a metà processo.

Il risultato: nessun limite pratico di durata video per il backend openai-api. Una riunione di 3 ore viene gestita automaticamente con ~18 chunk da 10 minuti ciascuno, senza intervento manuale.

### Raffinamento trascrizione con Claude

Whisper è eccellente ma non infallibile. I suoi errori tipici sono:
- Frasi conclusive inventate ("Grazie per aver guardato", "Sottotitoli realizzati da...")
- Ripetizioni consecutive di frasi identiche in corrispondenza di pause audio
- Punteggiatura assente o errata
- Nomi propri e termini tecnici traslitterati foneticamente

Il raffinamento Claude usa un prompt che specifica esattamente cosa correggere e cosa non toccare:

```
1. Correggi SOLO errori evidenti di punteggiatura e formattazione
2. Rimuovi allucinazioni Whisper note
3. Dividi in paragrafi dove il contesto cambia chiaramente
4. NON aggiungere, inventare o interpretare contenuto non presente
5. NON riassumere — restituisci il testo completo
```

Il constraint più importante è il quinto: il raffinamento non è un riassunto e non deve comprimere il testo. Il suo compito è editoriale, non semantico. Per questo motivo usa solo lo streaming base di Claude senza thinking né effort=high — costa meno e non ne ha bisogno.

Un guard impedisce il raffinamento se la trascrizione supera gli 80.000 caratteri (un'ora e mezza di parlato denso circa): sopra quella soglia si rischia di avvicinarsi ai limiti di contesto e il rischio di troncamento supera il beneficio della correzione.

---

## Docker e containerizzazione

Il Dockerfile usa `python:3.11-slim` come base e installa ffmpeg dal sistema operativo della distribuzione:

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

ARG WHISPER_BACKEND=faster-whisper
RUN pip install --no-cache-dir \
    $([ "$WHISPER_BACKEND" = "faster-whisper" ] && echo "faster-whisper" || \
      [ "$WHISPER_BACKEND" = "openai-whisper" ] && echo "openai-whisper" || \
      [ "$WHISPER_BACKEND" = "openai-api" ] && echo "openai") \
    && pip install --no-cache-dir anthropic python-dotenv

VOLUME ["/app/videos", "/app/output"]
ENTRYPOINT ["python", "analyze_video.py"]
```

La decisione di design più importante nel Dockerfile è l'`ARG WHISPER_BACKEND`: il backend Whisper viene scelto al **build time**, non a runtime. Questo mantiene l'immagine leggera (un solo backend installato invece di tutti e tre) e rende esplicita la configurazione. Cambiare backend richiede un rebuild, che è il comportamento corretto per una scelta architetturale come questa.

Il `docker-compose.yml` monta le cartelle locali come volumi:

```yaml
services:
  analyzer:
    build:
      context: .
      args:
        WHISPER_BACKEND: ${WHISPER_BACKEND:-faster-whisper}
    env_file: .env
    volumes:
      - ./videos:/app/videos:ro      # input read-only
      - ./output:/app/output         # output su filesystem locale
      - whisper_cache_hf:/root/.cache/huggingface   # modelli Whisper persistenti
      - whisper_cache_openai:/root/.cache/whisper
    command: []

volumes:
  whisper_cache_hf:
  whisper_cache_openai:
```

Due volumi named (`whisper_cache_hf` e `whisper_cache_openai`) persistono i modelli Whisper scaricati tra i run, evitando il re-download ad ogni esecuzione. Il volume `videos` è montato read-only per principio di privilegi minimi. L'output finisce su `./output` sul filesystem locale dell'host — i report non esistono solo nel container.

---

## Decisioni tecniche e trade-off

### Single-file vs. package

Ho scelto deliberatamente di mantenere il tool come single-file Python. Le ragioni:

1. **Portabilità**: si copia un file e funziona. Nessuna struttura di package da rispettare, nessun `__init__.py`, nessun path da configurare.
2. **Leggibilità**: tutto il flusso di esecuzione è tracciabile in un singolo file, dall'alto verso il basso.
3. **Semplicità di distribuzione**: `git clone` + `pip install -r requirements.txt` + `python analyze_video.py` — tre comandi.

Il trade-off ovvio è la manutenibilità a lungo termine: ~700 righe in un file singolo inizia a diventare pesante. Per un tool con questa natura (uno script operativo, non una libreria), il trade-off vale.

### Claude Opus 4.6 per tutto vs. modelli misti

Claude Opus 4.6 è il modello più capace della famiglia Claude ma anche il più costoso. Una scelta alternativa sarebbe usare Sonnet per le descrizioni frame (step 2, che è un task relativamente semplice di descrizione visiva) e Opus solo per l'analisi finale (step 3, che richiede ragionamento strutturato).

La documentazione del progetto suggerisce esplicitamente questa ottimizzazione come "Strategia 6" per ridurre i costi. Per i test iniziali ho usato Opus ovunque per massimizzare la qualità di base e stabilire un benchmark. La modifica è una singola costante nel codice.

### Perché ffmpeg e non OpenCV o librerie Python-native?

ffmpeg è lo standard industriale per il processing video. Rispetto a OpenCV o a librerie come `moviepy`:
- Supporto codec più ampio (tutti i format container che esistono)
- Nessuna dipendenza Python pesante (OpenCV è >100 MB, ffmpeg è già installato sulla maggior parte dei sistemi)
- Qualità di output controllata e predicibile
- Gestione robusta dei corner case (video corrotti, codec non standard, timestamp anomali)

L'unico svantaggio è che l'installazione su Windows richiede un passaggio manuale. Il codice include un `find_ffmpeg()` che cerca automaticamente nei path standard di WinGet, Chocolatey e Scoop prima di fallire, per ridurre la frizione su Windows.

### Caching delle descrizioni: risparmio reale in produzione

Il caching dello step 2 (se `_descrizioni.txt` esiste, salta Vision) è stata una delle feature più utili in pratica. Iterare sul prompt dell'analisi finale per ottenere un report migliore richiederebbe altrimenti di ripa-gare per tutte le chiamate Vision ogni volta. Con il caching, si paga Vision una volta e si può ottimizzare l'analisi finale gratuitamente.

Lo stesso principio si applica alla trascrizione audio: se `_trascrizione.txt` esiste, Whisper non viene rieseguito.

---

## Esempio reale: TED Talk di Clint Smith

Per validare la pipeline completa visivo+audio, ho usato il video incluso nel repository: "The Danger of Silence" di Clint Smith, TED@NYC 2014 (~4 minuti, 263 frame estratti).

**Comando:**

```bash
python analyze_video.py videos/ted_clint_smith.mp4 --audio --whisper-model base
```

**Trascrizione prodotta (estratto):**

> Dr. Martin Luther King, Jr., in a 1968 speech where he reflects upon the civil rights movement, states, "In the end, we will remember not the words of our enemies, but the silence of our friends."
>
> Silence is the residue of fear. It is feeling your flaws gut-wrench, guillotine your tongue. It is the air retreating from your chest because it doesn't feel safe in your lungs. Silence is Rwandan genocide. Silence is Katrina.
>
> So this year, instead of giving something up, I will live every day as if there were a microphone tucked under my tongue, a stage on the underside of my inhibition. Because who has to have a soapbox when all you've ever needed is your voice?

Il modello `base` di faster-whisper (74 MB, il più piccolo) ha prodotto zero allucinazioni su questo video. I nomi propri complessi ("Rwandan genocide", "Katrina") e le frasi poetiche dense sono stati trascritti correttamente.

**Highlights del report generato:**

Il report ha identificato autonomamente:

- La struttura retorica chiastica del discorso (A-B-C-X-C'-B'-A'): tre casi di silenzio nella narrativa riscritti come tre atti di parola nella risoluzione
- La gestualità come sistema semiotico parallelo al testo parlato (mani in tasca = silenzio/vulnerabilità, palmi aperti = offerta/domanda, pugno alzato = determinazione), correlata frame-per-frame
- La pausa finale di 6 secondi con oltre 2 minuti ancora sul timer, interpretata come scelta retorica deliberata — il silenzio scelto consapevolmente come opposto del silenzio per paura
- Un'osservazione critica sulla produzione: l'intro brandizzata di 12 secondi (4.6% del runtime totale) come rischio di drop-off su piattaforme digitali

Questa qualità di analisi — che correla dati visivi, dati audio e ragionamento strutturale — è il risultato diretto dell'approccio multimodale e dell'uso di thinking adattivo nello step finale.

---

## Casi d'uso verificati in produzione

Prima di questo tool, ho analizzato manualmente decine di sessioni video su sistemi CRM aziendali per documentare processi operativi. I video tipici mostravano operatori che gestivano richieste di connessione alla rete elettrica o gas nel sistema NET@SIU (Metamer). Ogni video durava 4-6 minuti e conteneva 40-60 step operativi.

Il tool ha prodotto report che identificavano:
- Tempi di caricamento elevati tra schermate (3-5 secondi per pagina)
- Inserimento ripetitivo di dati già presenti altrove nel sistema
- Assenza di autocomplete per campi tecnici (codici catastali)
- Validazione dei campi solo al salvataggio anziché in tempo reale

Questi erano esattamente gli elementi che avrei incluso in un'analisi manuale, ma prodotti in automatico in un tempo proporzionale alla durata del video invece che 3-4x di più.

Il caso d'uso del TED Talk mostra un tipo di analisi diverso: non un processo operativo ma una performance comunicativa. Il tool si adatta al contenuto senza configurazione specifica — l'analisi cambia natura perché il contenuto è diverso, non perché si sia cambiato il prompt.

---

## Documentazione MkDocs

Il progetto include documentazione completa con MkDocs Material, ospitata come GitHub Pages. La struttura copre:

- **Quick Start** — operativo in 5 minuti da zero
- **Architettura** — pipeline tecnica dettagliata con diagrammi ASCII per tutte e tre le modalità
- **Utilizzo** — tutti i flag CLI con esempi combinati
- **Configurazione** — tutte le variabili `.env` con spiegazione dei trade-off (quale modello Whisper scegliere, quando usare quale backend)
- **Audio Transcription** — guida dedicata ai tre backend con requisiti, qualità, costi comparati
- **Docker** — quick start, build options, volumi, note su GPU
- **Output** — formato dettagliato di ogni file generato
- **API Costs** — tabelle di stima costo per modalità, durata e fps
- **Examples** — output reali con estratti di trascrizioni e report
- **Troubleshooting** — 14 errori comuni con causa e soluzione

---

## Struttura del codebase

```
ai-report-video-analizer/
├── analyze_video.py          # ~700 righe — tutto il tool
├── requirements.txt          # core deps + 3 gruppi Whisper opzionali
├── .env.example              # template con commenti dettagliati
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── videos/
│   └── ted_clint_smith.mp4   # video esempio incluso (TED, CC BY-NC-ND)
├── output/                   # generato a runtime (gitignored)
└── docs/                     # MkDocs Material
    ├── index.md
    ├── quickstart.md
    ├── architettura.md
    ├── utilizzo.md
    ├── configurazione.md
    ├── audio.md              # nuovo: guide Whisper backends
    ├── docker.md             # nuovo: containerizzazione
    ├── output.md
    ├── esempi.md
    ├── costi.md
    └── troubleshooting.md
```

La struttura di `analyze_video.py` segue un ordine logico preciso:

```
Righe   1–67   Docstring, import, costanti, WHISPER config
Righe  68–127  ffmpeg utils + extract_frames()
Righe 128–160  extract_audio()
Righe 161–350  transcribe_audio() + 3 backend + compress/chunk helpers
Righe 351–468  Claude Vision: describe_frames_batch()
Righe 469–590  Claude Audio: refine_transcript() + analyze_audio_only()
Righe 591–660  analyze_process() — analisi finale visivo (+ transcript opzionale)
Righe 661–820  analyze_video() — orchestratore principale
Righe 821–917  main() — CLI argparse + validazione
```

---

## Cosa ho imparato costruendo questo tool

**1. Il batching è tutto**

La decisione su quanti frame inviare per chiamata Vision ha impatto sia sul costo che sulla qualità. Troppi frame e Claude perde dettagli sui singoli. Troppo pochi e il costo si moltiplica. 10 frame è un punto di equilibrio empirico buono per la maggior parte dei casi, ma la granularità deve poter essere configurata dall'utente — non esiste un valore universale.

**2. Il caching non è un'ottimizzazione, è una necessità**

In fase di sviluppo, si itera continuamente sul prompt dell'analisi finale. Senza caching delle descrizioni, ogni iterazione costerebbe l'intero step Vision (che per un video da 10 minuti a 1 fps sono 600 chiamate con immagini base64). Il caching trasforma il costo di sviluppo da lineare in quasi-zero per le iterazioni successive alla prima.

**3. Lazy import come pattern per dipendenze opzionali**

Lo script deve funzionare senza nessun pacchetto Whisper installato — il feature audio è opt-in. L'import a livello di modulo farebbe crashare lo script all'avvio se il pacchetto mancasse. Il lazy import (dentro la funzione, al momento dell'uso) risolve questo in modo elegante e produce un messaggio di errore chiaro invece di un traceback incomprensibile.

**4. L'integrazione audio/visivo amplifica la qualità dell'analisi**

Questa è stata la sorpresa più interessante del test sul TED Talk. Il report prodotto in modalità `--audio` era qualitativamente superiore a quello prodotto in solo visivo, non solo per l'aggiunta dei contenuti verbali, ma perché il modello poteva **correlare** gesti visivi con parole pronunciate — qualcosa che né la sola trascrizione né la sola analisi visiva avrebbe potuto fare.

**5. Il raffinamento Claude della trascrizione Whisper è necessario in produzione**

Whisper produce testi di qualità sorprendente, ma le sue allucinazioni caratteristiche (frasi conclusive false, ripetizioni) sono abbastanza sistematiche da essere fastidiose in un documento professionale. Il raffinamento Claude non è un lusso ma una correzione necessaria per portare l'output a qualità documento.

**6. I limiti API si risolvono con preprocessing, non con workaround**

Il limite di 25 MB dell'API OpenAI Whisper sembrava un problema serio per video lunghi. La soluzione elegante è stata non cercare workaround nell'API (non esistono) ma ridurre il problema alla fonte con compressione audio. A 32 kbps per parlato vocale, la qualità per la trascrizione è identica all'originale WAV, ma il file è 18 volte più piccolo. Il chunking automatico per i casi estremi è una rete di sicurezza, non il meccanismo principale.

---

## Stack tecnologico

| Componente | Tecnologia | Note |
|---|---|---|
| Runtime | Python 3.11+ | f-strings, `Path`, `str \| None` type hints |
| AI Vision | Claude Opus 4.6 (Anthropic) | Adaptive thinking, effort=high |
| AI Analysis | Claude Opus 4.6 (Anthropic) | Streaming, prompt strutturato 5 sezioni |
| Audio transcription | faster-whisper / openai-whisper / OpenAI API | 3 backend intercambiabili |
| Audio refinement | Claude Opus 4.6 | No thinking, task editoriale |
| Video processing | ffmpeg | Frame extraction, audio extraction, mp3 compression, chunking |
| Container | Docker + docker-compose | python:3.11-slim, ARG WHISPER_BACKEND |
| Config | python-dotenv | `.env` file per API keys e configurazione |
| SDK | anthropic Python SDK | Streaming + thinking support |
| Docs | MkDocs Material | Tabs, admonitions, GitHub Pages |

---

## Costo operativo

Per un video tipico da 5 minuti a 1 fps (300 frame) in modalità visivo+audio con faster-whisper locale:

| Step | Costo |
|---|---|
| Whisper locale | $0 |
| Claude raffinamento trascrizione | ~$0.08 |
| Claude Vision (300 frame) | ~$0.33 |
| Claude analisi finale | ~$0.10 |
| **Totale** | **~$0.51** |

Per un video da 10 minuti con le stesse impostazioni: ~$0.93. Per meeting lunghi in modalità `--audio-only` (nessuna Vision), il costo scende drasticamente: un'ora di riunione con faster-whisper locale costa ~$0.35 in totale (solo Claude refinement + analisi).

La strategia di ottimizzazione costi più efficace è usare Sonnet invece di Opus per lo step Vision (descrizioni frame) mantenendo Opus per l'analisi finale: riduzione del costo step 2 di circa il 40% con impatto minimo sulla qualità complessiva.

---

## Roadmap e sviluppi futuri

Alcune direzioni di sviluppo identificate durante l'uso:

**Salvataggio incrementale delle descrizioni**: attualmente le descrizioni vengono salvate solo al completamento di tutti i batch. Un salvataggio batch-per-batch permetterebbe di riprendere da dove si era fermati in caso di interruzione senza perdere il lavoro parziale.

**Interfaccia web leggera**: un frontend Flask/FastAPI minimale con upload video, selezione opzioni e visualizzazione report in tempo reale via SSE — renderebbe il tool accessibile senza CLI.

**Template di prompt personalizzabili**: il prompt dell'analisi finale è hardcoded. Permettere template esterni (file `.txt` o variabile `.env`) darebbe flessibilità per use case specifici (analisi UX, audit compliance, documentazione tecnica) senza modificare il codice.

**Supporto GPU locale per Whisper**: faster-whisper supporta CUDA via CTranslate2. Un rilevamento automatico della GPU disponibile e un'ottimizzazione automatica del `compute_type` (float16 su GPU vs float32 su CPU) ridurrebbero i tempi di trascrizione di un ordine di grandezza su hardware appropriato.

---

## Repository

Il codice è disponibile su GitHub: [github.com/antoniotrento/ai-report-video-analizer](https://github.com/antoniotrento/ai-report-video-analizer)

Il repository include un video di esempio funzionante (`videos/ted_clint_smith.mp4`): clonare il repository, configurare la `ANTHROPIC_API_KEY` nel `.env`, installare `faster-whisper`, e il primo test è immediato:

```bash
git clone https://github.com/antoniotrento/ai-report-video-analizer
cd ai-report-video-analizer
cp .env.example .env
# inserire ANTHROPIC_API_KEY nel .env
pip install anthropic python-dotenv faster-whisper
python analyze_video.py videos/ted_clint_smith.mp4 --audio --whisper-model base
```

L'output arriva in `output/` in streaming real-time.
