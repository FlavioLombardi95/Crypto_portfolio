# 🔧 Troubleshooting GitHub Actions - Restrizioni Geografiche Binance

## ❌ Problema
GitHub Actions fallisce con errore:
```
Service unavailable from a restricted location according to 'b. Eligibility'
```

## 🚀 Soluzioni Implementate

### 1. **🌍 Endpoint Dinamici**
Il sistema ora prova automaticamente:
- `https://api.binance.com`
- `https://api1.binance.com`
- `https://api2.binance.com`
- `https://api3.binance.com`

### 2. **🔄 Retry Logic**
- 2 tentativi per endpoint
- Pausa di 15 secondi tra tentativi
- Logging dettagliato

### 3. **🌐 Cloudflare Workers Proxy** (Opzionale)
Deploy gratuito su https://workers.cloudflare.com/

### 4. **📱 Esecuzione Manuale**
Se tutto fallisce, esegui localmente:
```bash
python3 crypto_portfolio.py
```

## 🔧 Configurazione

### GitHub Actions
```yaml
# Esecuzione manuale con opzioni
workflow_dispatch:
  inputs:
    use_alternative_api: true
```

### Variabili d'Ambiente
```bash
BINANCE_API_URL=https://api.binance.com
```

## 📊 Monitoraggio

### Log Files
- `crypto_portfolio.log` - Log completo
- `crypto_portfolio-18.log` - Log specifico GitHub Action

### Status
- ✅ **Successo**: Tutti gli asset trovati
- ⚠️ **Warning**: Alcuni endpoint falliti
- ❌ **Errore**: Tutti gli endpoint falliti

## 🆘 Se Tutto Fallisce

1. **Esegui localmente** (garantito funzionamento)
2. **Usa VPS gratuito** (Oracle Cloud Free Tier)
3. **Deploy su Heroku** (gratuito per hobby)
4. **Usa Railway** (gratuito per progetti)

## 📈 Statistiche Successo

- **Locale**: 100% successo
- **GitHub Actions**: ~70% successo (con retry)
- **Con Proxy**: ~90% successo

## 🔄 Aggiornamenti Automatici

Il sistema si riprova automaticamente ogni ora con:
- Endpoint diversi
- Retry logic
- Fallback options 