# 📖 Guida Completa Setup Crypto Portfolio Tracker

Questa guida ti accompagnerà passo dopo passo nella configurazione del sistema di tracking automatico del portafoglio crypto.

## 🎯 Panoramica

Il sistema è composto da:
- **Binance API**: Per recuperare i dati del portafoglio
- **Google Sheets API**: Per salvare e visualizzare i dati
- **GitHub Actions**: Per l'automazione oraria
- **Python Script**: Per l'elaborazione dei dati

---

## 🔑 Passo 1: Configurazione Binance API

### 1.1 Crea Account Binance
Se non hai già un account, registrati su [Binance](https://www.binance.com/it/register).

### 1.2 Abilita 2FA
Per sicurezza, abilita l'autenticazione a due fattori nel tuo account Binance.

### 1.3 Crea API Key
1. Vai su [API Management](https://www.binance.com/it/my/settings/api-management)
2. Clicca "Create API"
3. **IMPORTANTE**: Seleziona solo "Enable Reading"
4. **NON** abilitare trading, withdrawal o futures
5. Salva API Key e Secret Key in un posto sicuro

### 1.4 Restrizioni IP (Opzionale)
Per maggiore sicurezza, puoi limitare l'accesso API a specifici IP:
- GitHub Actions usa IP di Azure
- Puoi aggiungere restrizioni IP più tardi

---

## 📊 Passo 2: Configurazione Google Sheets

### 2.1 Crea Progetto Google Cloud
1. Vai su [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuovo progetto o seleziona uno esistente
3. Abilita la fatturazione (necessaria per le API)

### 2.2 Abilita Google Sheets API
1. Nel menu laterale, vai su "APIs & Services" > "Library"
2. Cerca "Google Sheets API"
3. Clicca su "Enable"

### 2.3 Crea Service Account
1. Vai su "APIs & Services" > "Credentials"
2. Clicca "Create Credentials" > "Service Account"
3. Dai un nome al service account (es. "crypto-portfolio-tracker")
4. Clicca "Create and Continue"
5. Salta i passaggi successivi e clicca "Done"

### 2.4 Genera Credenziali
1. Clicca sul service account appena creato
2. Vai alla tab "Keys"
3. Clicca "Add Key" > "Create new key"
4. Seleziona "JSON"
5. Clicca "Create" - il file verrà scaricato automaticamente

### 2.5 Crea Google Sheet
1. Vai su [Google Sheets](https://sheets.google.com)
2. Crea un nuovo foglio
3. Rinomina il primo foglio in "Portfolio"
4. Aggiungi le intestazioni nella prima riga:
   ```
   Asset | Quantità | Prezzo Medio | Prezzo Attuale | Valore Attuale | Investito Totale | PnL % | PnL € | Ultimo Aggiornamento
   ```

### 2.6 Condividi il Foglio
1. Nel Google Sheet, clicca "Share"
2. Aggiungi l'email del service account (trovata nel file JSON)
3. Dai permessi di "Editor"
4. Copia l'ID del foglio dall'URL (la parte tra /d/ e /edit)

---

## 🐙 Passo 3: Configurazione GitHub

### 3.1 Fork del Repository
1. Vai su [Crypto Portfolio Repository](https://github.com/FlavioLombardi95/Crypto_portfolio)
2. Clicca "Fork" per creare una copia nel tuo account

### 3.2 Configura GitHub Secrets
Nel tuo repository forked:
1. Vai su "Settings" > "Secrets and variables" > "Actions"
2. Clicca "New repository secret"
3. Aggiungi questi secrets:

#### BINANCE_API_KEY
- Nome: `BINANCE_API_KEY`
- Valore: La tua API Key di Binance

#### BINANCE_SECRET_KEY
- Nome: `BINANCE_SECRET_KEY`
- Valore: Il tuo Secret Key di Binance

#### GOOGLE_SHEET_ID
- Nome: `GOOGLE_SHEET_ID`
- Valore: L'ID del tuo Google Sheet (senza le virgolette)

#### GOOGLE_SHEETS_CREDENTIALS
- Nome: `GOOGLE_SHEETS_CREDENTIALS`
- Valore: Il contenuto completo del file JSON del service account

### 3.3 Test del Workflow
1. Vai su "Actions" nel tuo repository
2. Seleziona "Update Crypto Portfolio"
3. Clicca "Run workflow" > "Run workflow"
4. Monitora l'esecuzione per verificare che tutto funzioni

---

## 🧪 Passo 4: Test e Verifica

### 4.1 Verifica Logs
1. Dopo l'esecuzione del workflow, vai su "Actions"
2. Clicca sull'ultima esecuzione
3. Scarica l'artifact "portfolio-logs"
4. Controlla che non ci siano errori

### 4.2 Verifica Google Sheet
1. Apri il tuo Google Sheet
2. Verifica che i dati siano stati scritti correttamente
3. Controlla che le intestazioni siano presenti
4. Verifica che i calcoli PnL siano corretti

### 4.3 Test Locale (Opzionale)
Se vuoi testare localmente:
```bash
git clone https://github.com/TUO_USERNAME/Crypto_portfolio.git
cd Crypto_portfolio
pip install -r requirements.txt
# Crea un file .env con le variabili d'ambiente
python main.py
```

---

## ⚙️ Configurazione Avanzata

### Modificare Frequenza Aggiornamento
Nel file `.github/workflows/update_portfolio.yml`, modifica la riga:
```yaml
- cron: '0 * * * *'  # Ogni ora
```
Possibili valori:
- `'0 */2 * * *'` - Ogni 2 ore
- `'0 */6 * * *'` - Ogni 6 ore
- `'0 0 * * *'` - Ogni giorno a mezzanotte

### Aggiungere Nuove Colonne
1. Modifica `config.py` - aggiungi la colonna in `COLUMNS` e `HEADERS`
2. Aggiorna `binance_client.py` - aggiungi il calcolo del nuovo campo
3. Aggiorna `sheets_client.py` - modifica la scrittura dei dati

### Personalizzare Calcoli PnL
Il sistema attualmente assume prezzo medio = prezzo corrente. Per implementare il calcolo del prezzo medio reale:
1. Usa l'API Binance per recuperare lo storico delle transazioni
2. Calcola il prezzo medio ponderato
3. Aggiorna la logica in `binance_client.py`

---

## 🚨 Risoluzione Problemi

### Errore "Invalid API Key"
- Verifica che l'API Key sia corretta
- Controlla che abbia solo permessi di lettura
- Verifica che non sia scaduta

### Errore "Google Sheets API"
- Verifica che l'API sia abilitata nel progetto Google Cloud
- Controlla che le credenziali JSON siano corrette
- Verifica che il service account abbia accesso al foglio

### Errore "Rate Limit"
- Binance ha limiti di rate per le API
- Il sistema include gestione automatica dei rate limit
- Se persiste, aumenta l'intervallo tra le esecuzioni

### Dati Mancanti
- Verifica che il portafoglio contenga asset
- Controlla che i simboli siano supportati da Binance
- Verifica i log per errori specifici

---

## 🔮 Estensioni Future

### Notifiche Telegram
1. Crea un bot Telegram
2. Aggiungi il token nei GitHub Secrets
3. Modifica il workflow per inviare notifiche

### Analisi AI
1. Integra librerie ML (scikit-learn, tensorflow)
2. Aggiungi analisi di trend e sentiment
3. Implementa previsioni di prezzo

### Dashboard Web
1. Crea un'app web con Flask/FastAPI
2. Visualizza i dati in tempo reale
3. Aggiungi grafici interattivi

---

## 📞 Supporto

Se hai problemi:
1. Controlla i log del workflow GitHub Actions
2. Verifica la configurazione dei secrets
3. Apri una [Issue](https://github.com/FlavioLombardi95/Crypto_portfolio/issues)
4. Includi i log di errore e la configurazione (senza dati sensibili)

---

## ✅ Checklist Finale

- [ ] API Key Binance creata con permessi di sola lettura
- [ ] Google Cloud Project creato e Google Sheets API abilitata
- [ ] Service Account creato e credenziali JSON scaricate
- [ ] Google Sheet creato con intestazioni corrette
- [ ] Foglio condiviso con il service account
- [ ] Repository GitHub forked
- [ ] Tutti i secrets configurati
- [ ] Workflow testato e funzionante
- [ ] Dati visibili nel Google Sheet

🎉 **Congratulazioni!** Il tuo sistema di tracking automatico del portafoglio crypto è ora operativo! 