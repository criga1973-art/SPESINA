# 📝 PROMEMORIA REGOLE PROGETTO SPESINA

Questo file serve come memoria storica per le prossime sessioni di sviluppo. **NON USARE STRUMENTI ESTERNI (Adobe, Browser, ecc.)**.

### 📸 GESTIONE IMMAGINI
- **Tool**: Usare `process_rembg.py` per prodotti premium o complessi (rimozione sfondo AI). Usare `process_product.py` per ritagli rettangolari semplici.
- **Workflow**: Caricare lo screenshot in `Desktop/screenspesina` -> Elaborare -> Salvare in `img/`.
- **Standard Immagini**: 1000x1000 pixel, sfondo bianco (#FFFFFF), prodotto centrato, massima pulizia dai bordi.
- **Design Card Minimal**: Le descrizioni dei prodotti (`info.d` o `info.fullDesc`) NON devono essere mostrate direttamente sulla card. Consultabili esclusivamente tramite il tasto "Info" (modal).
- **Dati Tecnici**: Ogni prodotto deve essere arricchito con EAN-13, formato (L, gr, ml) e dettagli tecnici completi nel modal.
- **Cleanup**: Cancellare i file in `screenspesina` solo dopo approvazione dell'utente.

### 💻 SVILUPPO WEBAPP (index.html)
- **Struttura**: Navigazione a cartelle (Sub-folders) per categorie complesse (Pasta, Bevande).
- **Stile**: Design premium, icone emoji di fallback se manca la foto reale.
- **Labels**: Per la Pasta, mostrare sempre l'etichetta "500g" accanto al prezzo.

### 📁 FILE CHIAVE
- `index.html`: Codice sorgente dell'app.
- `process_rembg.py`: Script Python per rimozione sfondo AI.
- `process_product.py`: Script Python per ritaglio manuale rettangolare.
- `standardize_img.py`: Script per processare la cartella `img/` in batch.
- `img/original_backup/`: Archivio foto originali.

### ?? PUBBLICAZIONE & TEST
- **Maintenance Mode**: Il file index.html deve avere sempre MAINTENANCE_MODE = true fino al lancio ufficiale.
- **Preview Tecnica**: Per testare il sito live bypassando la manutenzione, aggiungere sempre ?preview=true allURL (es. spesina.it/?preview=true).
- **Deploy**: Ogni modifica approvata deve essere caricata su GitHub tramite git push per lggiornamento automatico su Vercel.
