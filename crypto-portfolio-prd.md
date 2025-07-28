# 📄 Product Requirements Document (PRD)

## 🧠 Progetto: Crypto Portfolio Tracker AI – Automazione via Binance + Google Sheets

---

### 🎯 1. Obiettivo del Prodotto

Costruire un sistema automatizzato e personalizzato che:

- Recupera i dati di portafoglio da Binance via API
- Calcola il costo medio di acquisto e profit/loss per ogni asset
- Scrive e aggiorna i dati in un Google Sheet ogni ora
- Consente il monitoraggio semplice e visivo del portafoglio in tempo reale
- Prepara il terreno per l’integrazione futura con modelli AI per analisi predittiva o segnali operativi

---

### 🛠️ 2. Caratteristiche Principali (Feature List)

| Feature                       | Descrizione                                                                 |
|------------------------------|-----------------------------------------------------------------------------|
| 🔌 Connessione a Binance API | Lettura automatica di asset, quantità, prezzo di acquisto                  |
| 📈 Calcolo PnL per asset     | Calcolo di profitto/perdita per ogni token e del totale del portafoglio    |
| 📊 Scrittura in Google Sheets| Aggiornamento automatico dei dati ogni ora in un foglio predefinito        |
| ⏱️ Automazione via GitHub Actions | Trigger orario per lo script senza necessità di server               |
| 🧠 Estendibilità AI-ready    | Base strutturata per analisi futura (es. trend, sentiment, previsioni)     |

---

### 🧩 3. Architettura e Stack Tecnologico

| Componente     | Tecnologia                           |
|----------------|--------------------------------------|
| API dati       | Binance REST API (Spot Wallet)       |
| Elaborazione   | Python 3.x (script principale)        |
| Output         | Google Sheets (via Google Sheets API)|
| Automazione    | GitHub Actions (workflow YAML)        |
| Sicurezza      | API Key Binance + GitHub Secrets     |

---

### 📐 4. Struttura del Google Sheet

| Colonna             | Contenuto                                            |
|---------------------|------------------------------------------------------|
| Asset               | Simbolo (es. BTC, ETH)                               |
| Quantità            | Quantità attualmente posseduta                       |
| Prezzo Medio        | Prezzo medio di acquisto                             |
| Prezzo Attuale      | Prezzo corrente (live)                               |
| Valore Attuale      | Quantità × Prezzo attuale                            |
| Investito Totale    | Quantità × Prezzo medio                              |
| PnL %               | ((Valore attuale - Investito) / Investito) × 100    |
| PnL €               | Valore attuale - Investito                           |
| Ultimo Aggiornamento| Timestamp                                            |

---

### 🔐 5. Sicurezza & Privacy

- Nessuna scrittura su Binance: solo lettura
- API Key e Secret salvate nei GitHub Secrets
- Google Sheets accessibile solo via OAuth (token service account)

---

### 🕒 6. Scheduling & Frequenza aggiornamento

- Frequenza: ogni 1 ora (`cron` via GitHub Actions)
- Modalità fallback: esecuzione manuale da GitHub (`workflow_dispatch`)

---

### 🔮 7. Estensioni future (AI e altro)

| Idea                   | Descrizione                                                              |
|------------------------|--------------------------------------------------------------------------|
| 📢 Notifiche Telegram  | Alert automatici per target di profit/loss o movimenti forti            |
| 🧠 AI Analisi          | Suggerimenti AI basati su trend storici, volumi, sentiment               |
| 🔍 Analisi ROI storica | Tracking del rendimento storico per asset e intervalli temporali         |
| 📉 Previsione prezzi   | Integrazione con modelli AI/ML (es. Prophet, LSTM, transformers)         |

---

### ✅ 8. Deliverable tecnici

- [ ] Script Python: recupero dati Binance + scrittura Google Sheet
- [ ] File `.yaml`: GitHub Actions con `schedule` e `workflow_dispatch`
- [ ] Google Sheet Template con intestazioni preimpostate
- [ ] Istruzioni `README.md` per:
  - Creazione API Binance
  - Setup Google API e service account
  - Configurazione GitHub repo e secrets

---

### 🧪 9. Criteri di accettazione

- ✅ Google Sheet aggiornato ogni ora con dati reali
- ✅ Dati corretti su quantità, prezzo medio, PnL
- ✅ Script eseguibile manualmente da GitHub
- ✅ Setup possibile in meno di 30 minuti con guida fornita
