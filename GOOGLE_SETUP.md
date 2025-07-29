# 🔧 Setup Google Sheets - Guida Completa

## 📋 Prerequisiti

- Account Google
- Google Cloud Project
- Google Sheet esistente

## 🚀 Passo 1: Google Cloud Console

1. **Apri Google Cloud Console:**
   ```
   https://console.cloud.google.com/
   ```

2. **Crea un nuovo progetto:**
   - Clicca sul selettore progetti in alto
   - "New Project"
   - Nome: `crypto-portfolio-tracker`
   - Clicca "Create"

## 🔑 Passo 2: Service Account

1. **Vai su IAM & Admin → Service Accounts:**
   ```
   https://console.cloud.google.com/iam-admin/serviceaccounts
   ```

2. **Crea Service Account:**
   - Clicca "Create Service Account"
   - Nome: `crypto-portfolio-tracker`
   - Descrizione: `Service account per Crypto Portfolio Tracker`
   - Clicca "Create and Continue"

3. **Assegna permessi:**
   - Ruolo: "Editor"
   - Clicca "Continue"
   - Clicca "Done"

4. **Crea chiave JSON:**
   - Clicca sul service account creato
   - Tab "Keys" → "Add Key" → "Create new key"
   - Formato: JSON
   - Clicca "Create"
   - **Scarica il file JSON** (importante!)

## 📊 Passo 3: Google Sheets API

1. **Abilita API:**
   - Vai su "APIs & Services" → "Library"
   - Cerca "Google Sheets API"
   - Clicca "Enable"

## 📝 Passo 4: Configura Google Sheet

### 4.1 Rinomina Foglio
- Apri il tuo Google Sheet
- Rinomina il primo foglio in "Portfolio"

### 4.2 Aggiungi Intestazioni
Nella riga 1, aggiungi queste colonne:

| A | B | C | D | E | F | G | H | I | J | K | L |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Asset | Quantità | Prezzo Medio | Prezzo Attuale | Valore Attuale | Investito Totale | PnL % | PnL € | Fonte | Tipo | APR % | Ultimo Aggiornamento |

### 4.3 Condividi con Service Account
1. Clicca "Condividi" (in alto a destra)
2. Aggiungi l'email del service account:
   ```
   crypto-portfolio-tracker@your-project-id.iam.gserviceaccount.com
   ```
3. Permessi: "Editor"
4. Clicca "Send"

## ⚙️ Passo 5: Configura Credenziali Locali

### 5.1 Aggiorna .env
Aggiungi queste righe al tuo file `.env`:

```bash
# Google Sheets Configuration
GOOGLE_SHEET_ID=1qz8T1p1ji1FuuGIWtfnbTNf3rB8gT7_j1u0u88EgW-M
GOOGLE_SHEETS_CREDENTIALS={"type":"service_account","project_id":"your_project_id","private_key_id":"your_private_key_id","private_key":"-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n","client_email":"crypto-portfolio-tracker@your_project_id.iam.gserviceaccount.com","client_id":"your_client_id","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/crypto-portfolio-tracker%40your_project_id.iam.gserviceaccount.com"}
```

### 5.2 Come ottenere le credenziali JSON
1. Apri il file JSON scaricato dal Service Account
2. Copia tutto il contenuto
3. Sostituisci il valore di `GOOGLE_SHEETS_CREDENTIALS` con il contenuto JSON

## 🧪 Passo 6: Test

Esegui il test per verificare la configurazione:

```bash
python3 test_google_sheets.py
```

## ✅ Risultato Atteso

Se tutto è configurato correttamente, vedrai:
```
🔍 Test Google Sheets
==============================
✅ Connessione Google Sheets riuscita!
📊 Intestazioni trovate: 12
📝 Prime intestazioni: ['Asset', 'Quantità', 'Prezzo Medio', 'Prezzo Attuale', 'Valore Attuale']...
✅ Test scrittura riuscito!
🧹 Rimuovi la riga di test dal Google Sheet
```

## 🚨 Risoluzione Problemi

### Errore: "GOOGLE_SHEETS_CREDENTIALS non trovato"
- Verifica che il file `.env` contenga le credenziali JSON
- Assicurati che il JSON sia su una singola riga

### Errore: "GOOGLE_SHEET_ID non trovato"
- Verifica che l'ID del Google Sheet sia corretto
- L'ID è nella URL: `https://docs.google.com/spreadsheets/d/ID/edit`

### Errore: "Access denied"
- Verifica che il Service Account abbia accesso al Google Sheet
- Controlla che l'email del Service Account sia aggiunta come editor

## 🎯 Prossimi Passi

Dopo aver completato il setup:
1. Testa il sistema completo: `python3 main.py`
2. Configura GitHub Secrets per l'automazione
3. Testa GitHub Actions 