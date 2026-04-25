# Regole Gestione Dati Spesina

Per garantire un catalogo pulito e professionale, seguiamo queste regole di gestione:

## 1. Visibilità e Filtri
- **Categoria `archivio`**: Qualsiasi prodotto assegnato a questa categoria viene automaticamente ESCLUSO dalla navigazione e dai risultati della ricerca globale. Serve per "accantonare" prodotti senza eliminarli definitivamente dal database.
- **Categoria `da-assegnare`**: Prodotti in attesa di lavorazione. Non dovrebbero apparire nelle categorie principali.

## 2. Standard Immagini
- **Formato**: WebP (per massima velocità e leggerezza).
- **Dimensioni**: 1000x1000 pixel (quadrato).
- **Sfondo**: Colore solido `#E6E6E6` (grigio chiarissimo premium).
- **Posizionamento**: Prodotto centrato, senza bordi Google Lens o icone UI.

## 3. Organizzazione Categorie
- **Brand**: Il valore del campo `brand` nel database deve corrispondere esattamente al nome della sottocartella definita in `index.html` (es. `Barilla`, `De Cecco`, `Voiello`).
- **Varie**: Prodotti come chewing gum (Vivident, Daygum) vanno in `category: 'varie'` e `brand: 'Varie'`.

## 4. Ricerca
- La ricerca filtra per Nome, Brand ed EAN, ma rispetta sempre il filtro di esclusione dell'archivio.
