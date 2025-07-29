# ⏰ Setup Cron Locale

## 🚀 Esecuzione Automatica Locale

### Setup Cron Job

1. **Apri Terminal**
2. **Edita crontab**:
   ```bash
   crontab -e
   ```

3. **Aggiungi questa riga** (aggiorna ogni ora):
   ```bash
   0 * * * * cd /Users/flavio.lombardi/Desktop/crypto-portfolio-update/Crypto_portfolio && python3 crypto_portfolio.py >> crypto_portfolio.log 2>&1
   ```

4. **Salva e esci** (Ctrl+X, Y, Enter)

### Verifica Setup

```bash
# Controlla cron jobs attivi
crontab -l

# Controlla log
tail -f crypto_portfolio.log
```

### Esecuzione Manuale

```bash
cd /Users/flavio.lombardi/Desktop/crypto-portfolio-update/Crypto_portfolio
python3 crypto_portfolio.py
```

## ✅ Risultato

- **Aggiornamento automatico**: Ogni ora
- **Log completo**: In crypto_portfolio.log
- **Funzionamento garantito**: Locale sempre funziona
- **Costo**: €0

## 🆘 Troubleshooting

- **Computer spento**: Nessun aggiornamento
- **Internet down**: Retry automatico
- **Errori**: Controlla log file 