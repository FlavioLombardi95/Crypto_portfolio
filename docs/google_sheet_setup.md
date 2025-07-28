# 📊 Configurazione Google Sheet Specifica

## ID del Foglio di Calcolo

Il Google Sheet da utilizzare è: **1qz8T1p1ji1FuuGIWtfnbTNf3rB8gT7_j1u0u88EgW-M**

URL completo: https://docs.google.com/spreadsheets/d/1qz8T1p1ji1FuuGIWtfnbTNf3rB8gT7_j1u0u88EgW-M/edit?usp=sharing

## Passi per la Configurazione

### 1. Apri il Foglio
1. Vai all'URL: https://docs.google.com/spreadsheets/d/1qz8T1p1ji1FuuGIWtfnbTNf3rB8gT7_j1u0u88EgW-M/edit?usp=sharing
2. Se richiesto, accedi con il tuo account Google

### 2. Rinomina il Primo Foglio
1. Clicca sul nome del foglio (probabilmente "Foglio1")
2. Rinominalo in **"Portfolio"** (esatto, con la P maiuscola)

### 3. Aggiungi le Intestazioni
Nella prima riga (A1:I1), aggiungi queste intestazioni:

| A | B | C | D | E | F | G | H | I |
|---|---|---|---|---|---|---|---|---|
| Asset | Quantità | Prezzo Medio | Prezzo Attuale | Valore Attuale | Investito Totale | PnL % | PnL € | Ultimo Aggiornamento |

### 4. Formattazione Consigliata
- **Intestazioni**: Arial, 12pt, Bold, sfondo grigio chiaro
- **Dati**: Arial, 11pt
- **Colonne monetarie**: Formato valuta €
- **Colonna PnL %**: Formato percentuale
- **Colonna Quantità**: 8 decimali

### 5. Condivisione con Service Account
1. Clicca "Condividi" (in alto a destra)
2. Aggiungi l'email del service account (trovata nel file JSON delle credenziali)
3. Dai permessi di **"Editor"**
4. Clicca "Invia"

### 6. Configurazione GitHub Secrets
Nel tuo repository GitHub, aggiungi questo secret:

**GOOGLE_SHEET_ID**: `1qz8T1p1ji1FuuGIWtfnbTNf3rB8gT7_j1u0u88EgW-M`

## Verifica della Configurazione

### Test Manuale
1. Apri il foglio
2. Verifica che il nome del foglio sia "Portfolio"
3. Verifica che le intestazioni siano presenti
4. Verifica che il service account abbia accesso

### Test Automatico
1. Vai su GitHub Actions nel tuo repository
2. Esegui manualmente il workflow "Update Crypto Portfolio"
3. Verifica che i dati vengano scritti nel foglio

## Struttura Attesa dei Dati

Dopo l'esecuzione del sistema, il foglio dovrebbe contenere:

| Asset | Quantità | Prezzo Medio | Prezzo Attuale | Valore Attuale | Investito Totale | PnL % | PnL € | Ultimo Aggiornamento |
|-------|----------|--------------|----------------|----------------|------------------|-------|-------|---------------------|
| BTC   | 0.50000000 | 45000.00 | 48000.00 | 24000.00 | 22500.00 | 6.67% | 1500.00 | 2024-01-15 10:00:00 |
| ETH   | 2.00000000 | 2800.00 | 3000.00 | 6000.00 | 5600.00 | 7.14% | 400.00 | 2024-01-15 10:00:00 |
|       |           |           |            |            |              |       |        |                     |
| TOTALE |           |           |            | 30000.00 | 28100.00 | 6.76% | 1900.00 | 2024-01-15 10:00:00 |

## Risoluzione Problemi

### Errore "Sheet not found"
- Verifica che il nome del foglio sia esattamente "Portfolio"
- Controlla che l'ID del foglio sia corretto

### Errore "Permission denied"
- Verifica che il service account abbia permessi di Editor
- Controlla che l'email del service account sia corretta

### Dati non aggiornati
- Verifica che il workflow GitHub Actions sia stato eseguito
- Controlla i log del workflow per errori

## Note Importanti

1. **ID del foglio**: `1qz8T1p1ji1FuuGIWtfnbTNf3rB8gT7_j1u0u88EgW-M`
2. **Nome del foglio**: Deve essere esattamente "Portfolio"
3. **Permessi**: Il service account deve avere accesso di Editor
4. **Formato**: Le intestazioni devono essere nella prima riga (A1:I1)

## Supporto

Se hai problemi con la configurazione:
1. Controlla che tutti i passi siano stati seguiti correttamente
2. Verifica i permessi di condivisione
3. Controlla i log del workflow GitHub Actions
4. Apri una issue nel repository con i dettagli dell'errore 