# 🚀 Deploy Rapido Cloudflare Proxy (5 minuti)

## ⚡ Soluzione Immediata

**Problema**: GitHub Actions bloccato da Binance
**Soluzione**: Cloudflare Workers Proxy (gratuito)

## 📋 Passi (5 minuti)

### 1. **🌐 Crea Account Cloudflare** (1 minuto)
- Vai su: https://dash.cloudflare.com/sign-up
- Registrati con email
- Verifica email

### 2. **🔧 Crea Worker** (2 minuti)
- Vai su: https://workers.cloudflare.com/
- Clicca "Create a Worker"
- Nome: `binance-proxy`

### 3. **📝 Copia Codice** (1 minuto)
- Sostituisci tutto il codice con quello di `cloudflare_proxy.js`
- Clicca "Save and Deploy"

### 4. **🔑 Aggiungi Secret** (1 minuto)
- Copia l'URL del worker (es: `https://binance-proxy.your-name.workers.dev`)
- Vai su GitHub → Repository → Settings → Secrets
- Aggiungi: `CLOUDFLARE_PROXY_URL` = URL del worker

## ✅ Test Immediato

```bash
# Testa il proxy
curl "https://your-worker.workers.dev/ping"

# Dovrebbe restituire: {"serverTime":1234567890}
```

## 🎯 Risultato

- **✅ GitHub Actions**: Funzionerà di nuovo
- **✅ Gratuito**: 100,000 request/giorno
- **✅ Velocità**: Edge network globale
- **✅ Bypass**: Restrizioni geografiche

## 🔄 Prossimo Run

Il prossimo GitHub Action userà automaticamente:
1. Endpoint Binance diretti
2. **Cloudflare Proxy** (fallback)
3. Configurazione alternativa

## 🆘 Se Non Funziona

1. **Verifica URL**: Il worker è deployato?
2. **Testa manualmente**: `curl` al worker
3. **Controlla logs**: GitHub Actions logs
4. **Esegui locale**: `python3 crypto_portfolio.py` 