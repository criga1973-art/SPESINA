# Architettura e Regole dell'Ecosistema Spesina

## Architettura dell'Ecosistema
Se dovessi disegnare l'architettura di Spesina, la vedrei come un ecosistema dove tutte le parti ruotano attorno a un unico "Cuore" centrale (il database Supabase).

### Diagramma Concettuale
- **Interfacce Clienti**: Sito Web (`index.html`) -> Leggi/Scrivi Prodotti e Ordini -> Supabase Database
- **Interfacce Gestione**:
    - Spesina Bot (`spesina_bot.py`) -> Inserisce nuovi Prodotti -> Supabase Database
    - Telecomando (`telecomando.html`) -> Modifica Limiti e Blocchi -> Supabase Database
    - Master Picking -> Legge Ordini da preparare -> Supabase Database

### Spiegazione dei Ruoli
1. **Supabase (Il Cuore)**: È il centro di gravità. Tutto ciò che accade viene salvato qui. Se si spegne questo, si ferma tutto.
2. **Sito Web (La Vetrina)**: Legge i prodotti da Supabase e scrive gli ordini dei clienti.
3. **Spesina Bot (Il Magazziniere)**: Ti permette di caricare i prodotti velocemente su Supabase.
4. **Telecomando (La Console di Controllo)**: Ti permette di impostare i limiti e bloccare le fasce orarie scrivendo su Supabase.
5. **Master Picking (La Logistica)**: Legge gli ordini da Supabase per farti sapere cosa preparare.

---

## Regole di Lavoro e Linee Guida

- **Step by Step**: Procederemo un passo alla volta, senza fretta.
- **Test in Locale**: Tutto (o quasi) verrà testato su `localhost:8080` prima di essere considerato definitivo.
- **Guida per Non-Programmatori**: Ti darò istruzioni chiare e semplici su cosa fare. Quando necessario, ti chiederò di confermare le azioni o ti mostrerò cosa fare.
- **Controllo Ortografico**: Farò attenzione a eventuali errori di battitura o anomalie nei tuoi messaggi per evitare danni al codice o al database.
- **Regola del 95%**: Se non sono sicuro al 95% di quello che mi chiedi, mi fermerò e ti farò delle domande.
- **Infrastruttura Citata**: Supabase, GitHub, Vercel, Resend, Render e futuro dominio su Aruba.
