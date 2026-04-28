# TODO Domani - 29 Aprile

## 📧 Implementazione Ricevuta Post-Consegna
Obiettivo: Inviare una mail professionale e cordiale al cliente non appena l'ordine viene segnato come "Consegnato" dallo shopper.

### Task Tecnici:
- [ ] **Dati Cliente**: Implementare il recupero automatico dell'email del cliente durante il `finishOrder`.
- [ ] **Template HTML**: Creare un template email "Premium" con:
    - Logo Spesina (nuova versione).
    - Messaggio: "Grazie [Nome]! La tua spesa è a casa."
    - Box: "Pagamento Ricevuto: [Totale] €".
    - Tabella prodotti con icone/foto.
- [ ] **Edge Function**: Aggiornare la funzione `send-welcome` su Supabase per gestire il nuovo tipo di email `RECEIPT`.

### Note:
- La base tecnica è già pronta in `shopper.html` nella funzione `triggerReceipt()`.
