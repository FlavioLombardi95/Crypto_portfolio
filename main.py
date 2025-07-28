#!/usr/bin/env python3
"""
Script principale per Crypto Portfolio Tracker
Coordina il recupero dati da Binance e l'aggiornamento di Google Sheets
"""
import logging
import sys
from datetime import datetime
from config import Config
from binance_client import BinanceClient
from sheets_client import GoogleSheetsClient

def setup_logging():
    """Configura il sistema di logging"""
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format=Config.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('crypto_portfolio.log')
        ]
    )

def main():
    """Funzione principale"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Avvio Crypto Portfolio Tracker")
    logger.info(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Validazione configurazione
        if not Config.validate_config():
            logger.error("❌ Configurazione non valida. Uscita.")
            sys.exit(1)
        
        # Inizializzazione client
        logger.info("🔧 Inizializzazione client...")
        binance_client = BinanceClient()
        sheets_client = GoogleSheetsClient()
        
        # Test connessioni
        logger.info("🔍 Test connessioni...")
        if not binance_client.test_connection():
            logger.error("❌ Connessione a Binance fallita")
            sys.exit(1)
        
        if not sheets_client.test_connection():
            logger.error("❌ Connessione a Google Sheets fallita")
            sys.exit(1)
        
        # Recupero dati portafoglio
        logger.info("📊 Recupero dati portafoglio da Binance...")
        portfolio_data = binance_client.get_portfolio_data()
        
        if not portfolio_data:
            logger.warning("⚠️ Nessun asset trovato nel portafoglio")
            # Scrivi comunque le intestazioni per mantenere la struttura
            sheets_client.write_headers()
            logger.info("✅ Intestazioni scritte nel foglio")
        else:
            logger.info(f"✅ Recuperati dati per {len(portfolio_data)} asset")
            
            # Aggiornamento Google Sheets
            logger.info("📝 Aggiornamento Google Sheets...")
            
            # Pulisci il foglio (opzionale - commenta se vuoi mantenere i dati storici)
            # sheets_client.clear_sheet()
            
            # Scrivi intestazioni
            sheets_client.write_headers()
            
            # Scrivi dati portafoglio
            sheets_client.write_portfolio_data(portfolio_data)
            
            # Aggiungi riga di riepilogo
            sheets_client.add_summary_row(portfolio_data)
            
            # Log dei totali
            total_value = sum(item['current_value'] for item in portfolio_data)
            total_invested = sum(item['total_invested'] for item in portfolio_data)
            total_pnl = sum(item['pnl_euro'] for item in portfolio_data)
            
            logger.info(f"💰 Totale valore portafoglio: €{total_value:,.2f}")
            logger.info(f"💸 Totale investito: €{total_invested:,.2f}")
            logger.info(f"📈 PnL totale: €{total_pnl:,.2f}")
        
        logger.info("✅ Aggiornamento completato con successo!")
        
    except Exception as e:
        logger.error(f"❌ Errore durante l'esecuzione: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 