# 🚀 Crypto Portfolio Tracker AI

Sistema automatizzato per il tracking del portafoglio crypto tramite Binance API e Google Sheets.

## 📋 Caratteristiche

- 🔌 **Connessione Binance API**: Lettura automatica di asset, quantità e prezzi
- 📈 **Calcolo PnL**: Profitto/perdita per ogni token e totale portafoglio
- 📊 **Google Sheets Integration**: Aggiornamento automatico ogni ora
- ⏱️ **Automazione GitHub Actions**: Esecuzione schedulata senza server
- 🧠 **AI-Ready**: Base strutturata per analisi predittive future

## 🛠️ Setup Rapido

### 1. Prerequisiti

- Account Binance con API Key
- Account Google con Google Sheets API abilitata
- Repository GitHub

### 2. Configurazione Binance API

1. Vai su [Binance](https://www.binance.com/it/my/settings/api-management)
2. Crea una nuova API Key con permessi di **sola lettura**
3. Salva API Key e Secret

### 3. Configurazione Google Sheets

1. Vai su [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuovo progetto
3. Abilita Google Sheets API
4. Crea un Service Account
5. Scarica il file JSON delle credenziali
6. Condividi il Google Sheet con l'email del service account

### 4. Configurazione GitHub Secrets

Nel tuo repository GitHub, vai su Settings > Secrets and variables > Actions e aggiungi:

- `BINANCE_API_KEY`: La tua API Key di Binance
- `BINANCE_SECRET_KEY`: Il tuo Secret Key di Binance
- `GOOGLE_SHEETS_CREDENTIALS`: Il contenuto del file JSON del service account
- `GOOGLE_SHEET_ID`: L'ID del tuo Google Sheet

### 5. Google Sheet Template

Crea un Google Sheet con questa struttura:

| Asset | Quantità | Prezzo Medio | Prezzo Attuale | Valore Attuale | Investito Totale | PnL % | PnL € | Ultimo Aggiornamento |
|-------|----------|--------------|----------------|----------------|------------------|-------|-------|---------------------|
| BTC   | 0.5      | 45000        | 48000          | 24000          | 22500            | 6.67% | 1500  | 2024-01-15 10:00    |

## 📁 Struttura del Progetto

```
Crypto_portfolio/
├── README.md                 # Questo file
├── requirements.txt          # Dipendenze Python
├── main.py                   # Script principale
├── config.py                 # Configurazione
├── binance_client.py         # Client Binance API
├── sheets_client.py          # Client Google Sheets
├── .github/
│   └── workflows/
│       └── update_portfolio.yml  # GitHub Actions workflow
└── docs/
    └── setup_guide.md        # Guida dettagliata setup
```

## 🚀 Utilizzo

### Esecuzione Manuale

```bash
pip install -r requirements.txt
python main.py
```

### Esecuzione Automatica

Il sistema si aggiorna automaticamente ogni ora tramite GitHub Actions.

## 🔧 Configurazione Avanzata

Vedi [docs/setup_guide.md](docs/setup_guide.md) per istruzioni dettagliate.

## 🤝 Contributi

1. Fork del repository
2. Crea un branch per la feature (`git checkout -b feature/nuova-feature`)
3. Commit delle modifiche (`git commit -am 'Aggiunge nuova feature'`)
4. Push del branch (`git push origin feature/nuova-feature`)
5. Crea una Pull Request

## 📄 Licenza

Questo progetto è sotto licenza MIT. Vedi il file [LICENSE](LICENSE) per dettagli.

## 🆘 Supporto

Per problemi o domande:
- Apri una [Issue](https://github.com/FlavioLombardi95/Crypto_portfolio/issues)
- Controlla la [documentazione](docs/)

---

⭐ Se questo progetto ti è utile, considera di dargli una stella! 