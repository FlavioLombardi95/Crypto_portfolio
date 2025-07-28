# 🔧 Troubleshooting GitHub Actions - Binance API

## 🚨 Problema: Restrizioni Geografiche

### **Errore Tipico**
```
APIError(code=0): Service unavailable from a restricted location according to 'b. Eligibility' in https://www.binance.com/en/terms
```

### **Causa**
Binance blocca le richieste dai server di GitHub Actions per restrizioni geografiche. I server cloud di GitHub non sono autorizzati ad accedere all'API di Binance.

### **Soluzioni**

#### **Opzione 1: Esecuzione Locale (Raccomandato)**
Il sistema funziona perfettamente in locale. Usa:

```bash
python3 main.py
```

#### **Opzione 2: Self-Hosted Runner**
Configura un runner GitHub Actions su un server privato:

1. Vai su GitHub Repository → Settings → Actions → Runners
2. Clicca "New self-hosted runner"
3. Segui le istruzioni per installare su un server autorizzato

#### **Opzione 3: VPS/Cloud Server**
Esegui il script su un server VPS:

```bash
# Installa Python e dipendenze
pip install -r requirements.txt

# Esegui con cron
crontab -e
# Aggiungi: 0 * * * * cd /path/to/project && python3 main.py
```

#### **Opzione 4: Alternative Cloud**
Usa servizi che supportano Binance:
- **Railway.app**
- **Render.com**
- **Heroku** (con buildpack personalizzato)

### **Configurazione Cron Locale**

Per automatizzare l'esecuzione locale:

```bash
# Apri crontab
crontab -e

# Aggiungi questa riga per esecuzione ogni ora
0 * * * * cd /Users/flavio.lombardi/Desktop/crypto-portfolio-update/Crypto_portfolio && python3 main.py >> /tmp/crypto_portfolio.log 2>&1
```

### **Monitoraggio**

Controlla i log:
```bash
tail -f crypto_portfolio.log
```

### **Test Locale**

```bash
# Test connessione
python3 -c "from binance_client import BinanceClient; BinanceClient().test_connection()"

# Test completo
python3 main.py
```

## ✅ **Raccomandazione**

**Usa l'esecuzione locale con cron** per la massima affidabilità e controllo. 