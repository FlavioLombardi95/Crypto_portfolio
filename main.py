"""
Crypto Portfolio Tracker - Main Script
Aggiorna automaticamente il portafoglio crypto su Google Sheets (Spot + Simple Earn)
"""
import logging
import sys
from datetime import datetime
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

from config import Config
from binance_client import BinanceClient
from sheets_client import GoogleSheetsClient

def setup_logging():
    """Configura il logging"""
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
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🚀 Avvio Crypto Portfolio Tracker")
        logger.info(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. Validazione configurazione
        if not Config.validate_config():
            logger.error("❌ Configurazione non valida. Uscita.")
            return False
        
        # 2. Inizializzazione client
        binance_client = BinanceClient()
        sheets_client = GoogleSheetsClient()
        
        # 3. Test connessioni
        logger.info("🔍 Test connessioni...")
        
        if not binance_client.test_connection():
            logger.error("❌ Connessione a Binance fallita")
            return False
        
        if not sheets_client.test_connection():
            logger.error("❌ Connessione a Google Sheets fallita")
            return False
        
        logger.info("✅ Tutte le connessioni OK")
        
        # 4. Recupero dati portafoglio (Spot + Simple Earn)
        logger.info("📊 Recupero dati portafoglio...")
        portfolio_data = binance_client.get_portfolio_data()
        
        if not portfolio_data:
            logger.warning("⚠️ Nessun dato portafoglio trovato")
            return False
        
        logger.info(f"✅ Recuperati dati per {len(portfolio_data)} asset")
        
        # 5. Aggiornamento Google Sheets
        logger.info("📝 Aggiornamento Google Sheets...")
        
        # Pulisci il foglio
        sheets_client.clear_sheet()
        
        # Scrivi intestazioni
        sheets_client.write_headers()
        
        # Scrivi dati portafoglio
        sheets_client.write_portfolio_data(portfolio_data)
        
        # Aggiungi riga di riepilogo
        sheets_client.add_summary_row(portfolio_data)
        
        # 6. Log risultati
        total_value = sum(item['current_value'] for item in portfolio_data)
        total_invested = sum(item['total_invested'] for item in portfolio_data)
        total_pnl = sum(item['pnl_euro'] for item in portfolio_data)
        
        spot_assets = [item for item in portfolio_data if item.get('source') == 'Spot']
        earn_assets = [item for item in portfolio_data if 'Simple Earn' in item.get('source', '')]
        
        logger.info("🎉 Aggiornamento completato con successo!")
        logger.info(f"💰 Valore totale: €{total_value:,.2f}")
        logger.info(f"💸 Investito totale: €{total_invested:,.2f}")
        logger.info(f"📈 PnL totale: €{total_pnl:,.2f}")
        logger.info(f"📊 Asset Spot: {len(spot_assets)}")
        logger.info(f"📊 Asset Simple Earn: {len(earn_assets)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore durante l'esecuzione: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    setup_logging()
    success = main()
    sys.exit(0 if success else 1) 