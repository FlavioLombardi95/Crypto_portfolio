# 🌐 Deploy Cloudflare Workers Proxy (Gratuito)

## 🚀 Deploy Immediato

1. **Vai su**: https://workers.cloudflare.com/
2. **Crea account** (gratuito)
3. **Crea nuovo Worker**
4. **Copia il codice** da `cloudflare_proxy.js`
5. **Deploy** (gratuito)

## 📋 Passi Dettagliati

### Step 1: Account Cloudflare
- Registrati su https://dash.cloudflare.com/sign-up
- Verifica email

### Step 2: Workers Dashboard
- Vai su https://workers.cloudflare.com/
- Clicca "Create a Worker"

### Step 3: Codice
- Sostituisci tutto il codice con quello di `cloudflare_proxy.js`
- Clicca "Save and Deploy"

### Step 4: URL
- Copia l'URL del worker (es: `https://binance-proxy.your-name.workers.dev`)
- Aggiungi come secret in GitHub: `CLOUDFLARE_PROXY_URL`

## 🔧 Configurazione GitHub Actions

Aggiungi al workflow:
```yaml
env:
  CLOUDFLARE_PROXY_URL: ${{ secrets.CLOUDFLARE_PROXY_URL }}
```

## ✅ Test

Il proxy funziona così:
- `https://your-worker.workers.dev/ping` → `https://api.binance.com/ping`
- `https://your-worker.workers.dev/api/v3/ticker/price?symbol=BTCUSDT` → `https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT`

## 🎯 Risultato

- **Gratuito**: 100,000 request/giorno
- **Velocità**: Edge network globale
- **Bypass**: Restrizioni geografiche
- **Compatibilità**: Tutte le API Binance 