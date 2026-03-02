# Output

Per ogni video analizzato vengono prodotti **2 file** nella cartella `output/`, più gli screenshot opzionali.

---

## File 1: `_descrizioni.txt`

**Cosa è:** trascrizione visiva cronologica del video, frame per frame.

**Formato:**
```
Frame 1 (t=0.0s): Schermata iniziale dell'applicazione con menu di navigazione visibile a sinistra. L'utente non ha ancora eseguito azioni.

Frame 2 (t=1.0s): L'utente clicca sulla voce "Nuovo ordine" nel menu laterale. Si apre un form con campi vuoti.

Frame 3 (t=2.0s): Viene digitato il nome del cliente nel primo campo. Il campo mostra "Mario Rossi".

Frame 4 (t=3.0s): Il cursore si sposta sul campo "Prodotto". Appare un menu a tendina con l'elenco dei prodotti disponibili.
...
```

**A cosa serve:**
- Verifica rapida di cosa Claude ha visto in ogni momento
- Fonte dati per l'analisi del processo
- Utile per debug se l'analisi finale sembra imprecisa

---

## File 2: `_analisi.md`

**Cosa è:** report strutturato del processo, generato da Claude interpretando le descrizioni.

**Formato completo:**

```markdown
# Analisi Video: tutorial.mp4

## 1. OBIETTIVO DEL PROCESSO
L'utente sta creando un nuovo ordine nel sistema gestionale aziendale,
inserendo i dati del cliente, selezionando i prodotti e confermando l'ordine.

## 2. FLUSSO OPERATIVO — STEP BY STEP

1. **Accesso alla sezione ordini**
   - Azione: clic su "Nuovo ordine" nel menu laterale
   - Interfaccia: pannello di navigazione sinistro
   - Risultato: apertura form di inserimento ordine

2. **Inserimento dati cliente**
   - Azione: digitazione nome e dati anagrafici
   - Interfaccia: campi testo del form
   - Risultato: cliente "Mario Rossi" selezionato

3. **Selezione prodotti**
   - Azione: apertura menu a tendina e selezione prodotto
   - Interfaccia: dropdown con lista prodotti
   - Risultato: prodotto aggiunto alla riga ordine

4. **Conferma quantità**
   - Azione: modifica campo quantità
   - Interfaccia: campo numerico
   - Risultato: quantità impostata a 3 unità

5. **Salvataggio ordine**
   - Azione: clic su "Conferma ordine"
   - Interfaccia: pulsante primario in fondo al form
   - Risultato: ordine salvato, ID #10847 assegnato

## 3. ELEMENTI TECNICI IDENTIFICATI
- **Sistema:** ERP gestionale (interfaccia web)
- **Dati coinvolti:** anagrafica clienti, catalogo prodotti, magazzino
- **Tecnologie visibili:** applicazione web, form HTML standard

## 4. OSSERVAZIONI CRITICHE
- Il processo richiede 5 passaggi distinti per un ordine semplice
- Non è presente la funzione "ordine rapido" per clienti abituali
- La selezione prodotti con menu a tendina diventa lenta con cataloghi grandi
- Nessuna validazione in tempo reale dei campi (errori scoperti solo al salvataggio)

## 5. SUGGERIMENTI DI OTTIMIZZAZIONE
- Aggiungere un campo di ricerca clienti con autocompletamento
- Implementare "ordini recenti" per riutilizzare configurazioni precedenti
- Sostituire il dropdown prodotti con una ricerca full-text
- Aggiungere validazione live sui campi obbligatori
- Considerare un flusso "ordine rapido" in 2 step per clienti e prodotti già usati
```

---

## File 3: `output/frames/` *(opzionale)*

Disponibile solo con `--keep-frames`. Contiene gli screenshot PNG estratti:

```
output/
└── frames/
    └── tutorial/
        ├── frame_0001.png   ← t=0s
        ├── frame_0002.png   ← t=1s
        ├── frame_0003.png   ← t=2s
        └── ...
```

Ogni file è nominato `frame_NNNN.png` dove NNNN è il numero progressivo (corrispondente al timestamp nella descrizione).

---

## Riepilogo

| File | Dove | Sempre presente |
|---|---|---|
| `<nome>_descrizioni.txt` | `output/` | Sì |
| `<nome>_analisi.md` | `output/` | Sì |
| `frames/<nome>/frame_NNNN.png` | `output/frames/` | Solo con `--keep-frames` |
