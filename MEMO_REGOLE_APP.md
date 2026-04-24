# 📝 PROMEMORIA REGOLE PROGETTO SPESINA

Questo file serve come memoria storica per le prossime sessioni di sviluppo. **NON USARE STRUMENTI ESTERNI (Adobe, Browser, ecc.)**.

### 📸 GESTIONE IMMAGINI
- **Tool**: Usare `process_rembg.py` per tutti i prodotti. Scontornamento AI obbligatorio per isolare il prodotto.
- **Workflow**: Ricerca web immagine ufficiale -> `rembg` -> Canvas 1000x1000 -> Ottimizzazione WebP.
- **Standard Immagini**: **1000x1000 pixel**, sfondo grigio chiaro (**#E6E6E6**), prodotto centrato e "staccato" dai bordi.
- **Layout Card**: Immagine in alto, Nome Prodotto e Quantità (L, gr, ml) immediatamente sotto l'immagine. Prezzo bene in evidenza.
- **Design Card Minimal**: Le descrizioni lunghe (`info.d`) NON devono essere mostrate sulla card, ma solo nel modal "Info".
- **Dati Tecnici**: Ogni prodotto deve avere EAN-13, formato e dettagli tecnici (ingredienti/allergeni) caricati su Supabase.

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
