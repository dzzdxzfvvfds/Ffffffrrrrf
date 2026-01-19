# Ambulatorio Infermieristico - PRD

## Problema Originale
Sistema di gestione ambulatorio infermieristico con sincronizzazione Google Sheets.

### Requisiti Implementati (19/01/2026)
1. **Gestione Categorie Paziente PICC/MED**
   - Possibilità di abilitare/disabilitare PICC e MED indipendentemente
   - Un paziente può essere Solo PICC, Solo MED, oppure PICC + MED
   - Gli appuntamenti precedenti mantengono la loro categoria originale
   - Nuova opzione "Gestisci Categorie" nel dropdown menu paziente
   - Dialog con switch PICC/MED per attivare/disattivare categorie

2. **Sistema Timestamp Sincronizzazione**
   - Salvataggio timestamp di ogni sincronizzazione
   - Endpoint GET /api/sync/timestamp/{ambulatorio}
   - Tracciamento numero appuntamenti e pazienti sincronizzati

3. **Preservazione Modifiche Manuali**
   - Modifiche manuali agli appuntamenti importati vengono tracciate
   - Campo `manually_modified` su appuntamenti e pazienti
   - Collezione `manual_edits` per tracciare le modifiche
   - Modifiche manuali hanno priorità sui dati del foglio Google

## Architettura
- **Backend**: FastAPI (Python)
- **Frontend**: React + Tailwind CSS + Shadcn UI
- **Database**: MongoDB
- **Sincronizzazione**: Google Sheets (pubblico)

## Endpoint Implementati
- `PUT /api/patients/{id}/tipo` - Cambio tipo paziente
- `GET /api/sync/timestamp/{ambulatorio}` - Ottiene timestamp ultima sync
- `POST /api/sync/manual-edit` - Salva modifica manuale
- `GET /api/sync/manual-edits/{ambulatorio}` - Lista modifiche manuali

## Backlog
- P0: Nessuno
- P1: Implementare filtro per timestamp nel parsing Google Sheets
- P2: Dashboard statistiche modifiche manuali
