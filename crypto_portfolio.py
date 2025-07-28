#!/usr/bin/env python3
"""
Crypto Portfolio Tracker - Sistema Unificato
Gestisce portafogli Binance (Spot + Simple Earn) e aggiorna Google Sheets
"""
import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Importa librerie esterne
try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException
    from google.auth.transport.requests import Request
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    print(f"❌ Libreria mancante: {e}")
    print("Installa con: pip install -r requirements.txt")
    sys.exit(1)

# Carica variabili d'ambiente
load_dotenv()

class Config:
    """Configurazione centralizzata"""
    
    # Binance API
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
    BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
    
    # Google Sheets
    GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
    GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE')
    GOOGLE_SHEETS_CREDENTIALS = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
    
    # Sheet Configuration
    SHEET_NAME = 'Portfolio'
    START_ROW = 2
    
    # Headers
    HEADERS = [
        'Asset', 'Quantità', 'Prezzo Medio (USDT)', 'Prezzo Attuale (USDT)',
        'Valore Attuale (USDT)', 'Investito Totale (USDT)', 'PnL %', 'PnL USDT',
        'Fonte', 'Tipo', 'APR %', 'Ultimo Aggiornamento'
    ]
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    
    @classmethod
    def validate(cls) -> bool:
        """Valida configurazione"""
        required = ['BINANCE_API_KEY', 'BINANCE_SECRET_KEY', 'GOOGLE_SHEET_ID']
        missing = [var for var in required if not getattr(cls, var)]
        
        if missing:
            print(f"❌ Configurazioni mancanti: {', '.join(missing)}")
            return False
        
        if not cls.GOOGLE_SHEETS_CREDENTIALS_FILE and not cls.GOOGLE_SHEETS_CREDENTIALS:
            print("❌ Credenziali Google Sheets mancanti")
            return False
        
        return True

class BinanceManager:
    """Gestore per Binance API"""
    
    def __init__(self):
        self.client = Client(Config.BINANCE_API_KEY, Config.BINANCE_SECRET_KEY)
        self.logger = logging.getLogger('Binance')
    
    def test_connection(self) -> bool:
        """Testa connessione Binance"""
        try:
            self.client.get_server_time()
            self.logger.info("✅ Connessione Binance OK")
            return True
        except BinanceAPIException as e:
            if "restricted location" in str(e).lower():
                self.logger.error("❌ Binance non disponibile (restrizione geografica)")
                self.logger.info("💡 Usa esecuzione locale per GitHub Actions")
            else:
                self.logger.error(f"❌ Errore Binance: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Errore connessione: {e}")
            return False
    
    def get_portfolio_data(self) -> List[Dict]:
        """Recupera dati portafoglio completo (Spot + Simple Earn)"""
        try:
            portfolio_data = []
            
            # 1. Dati Spot
            spot_data = self._get_spot_data()
            portfolio_data.extend(spot_data)
            
            # 2. Dati Simple Earn
            earn_data = self._get_earn_data()
            portfolio_data.extend(earn_data)
            
            self.logger.info(f"📊 Asset totali trovati: {len(portfolio_data)}")
            
            # 3. Filtra asset con valore >= 0.01€ (più flessibile)
            # Nota: Gli asset LD* sono token di Launchpool distribuiti gratuitamente
            filtered_data = [item for item in portfolio_data if item['current_value'] >= 0.01]
            
            # 4. Ordina per valore
            filtered_data.sort(key=lambda x: x['current_value'], reverse=True)
            
            self.logger.info(f"✅ Portfolio filtrato: {len(filtered_data)} asset (valore >= 0.01€)")
            return filtered_data
            
        except Exception as e:
            self.logger.error(f"❌ Errore portfolio: {e}")
            raise
    
    def _get_spot_data(self) -> List[Dict]:
        """Recupera dati wallet Spot"""
        try:
            account = self.client.get_account()
            balances = account['balances']
            
            spot_data = []
            for balance in balances:
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total > 0:
                    asset = balance['asset']
                    current_price = self._get_current_price(asset)
                    
                    if current_price > 0:
                        current_value = total * current_price
                        avg_price = self._get_average_price(asset) or current_price
                        total_invested = total * avg_price
                        pnl = current_value - total_invested
                        pnl_percentage = (pnl / total_invested * 100) if total_invested > 0 else 0
                        
                        spot_data.append({
                            'asset': asset,
                            'quantity': total,
                            'avg_price': avg_price,
                            'current_price': current_price,
                            'current_value': current_value,
                            'total_invested': total_invested,
                            'pnl_percentage': pnl_percentage,
                            'pnl_euro': pnl,
                            'source': 'Spot',
                            'type': 'Spot',
                            'apr': 0
                        })
            
            self.logger.info(f"✅ Spot: {len(spot_data)} asset")
            return spot_data
            
        except Exception as e:
            self.logger.error(f"❌ Errore Spot: {e}")
            return []
    
    def _get_earn_data(self) -> List[Dict]:
        """Recupera dati Simple Earn"""
        try:
            earn_data = []
            
            # Flexible positions
            flexible = self.client.get_simple_earn_flexible_product_position()
            self.logger.debug(f"Flexible positions trovate: {len(flexible.get('rows', []))}")
            
            for pos in flexible.get('rows', []):
                asset = pos['asset']
                amount = float(pos['totalAmount'])
                
                if amount > 0:
                    current_price = self._get_current_price(asset)
                    
                    if current_price > 0:
                        current_value = amount * current_price
                        avg_price = self._get_average_price(asset) or current_price
                        total_invested = amount * avg_price
                        pnl = current_value - total_invested
                        pnl_percentage = (pnl / total_invested * 100) if total_invested > 0 else 0
                        apr = float(pos.get('latestAnnualPercentageRate', 0)) * 100
                        
                        earn_data.append({
                            'asset': asset,
                            'quantity': amount,
                            'avg_price': avg_price,
                            'current_price': current_price,
                            'current_value': current_value,
                            'total_invested': total_invested,
                            'pnl_percentage': pnl_percentage,
                            'pnl_euro': pnl,
                            'source': 'Simple Earn',
                            'type': 'Flexible',
                            'apr': apr
                        })
            
            # Locked positions
            locked = self.client.get_simple_earn_locked_product_position()
            self.logger.debug(f"Locked positions trovate: {len(locked.get('rows', []))}")
            
            for pos in locked.get('rows', []):
                asset = pos['asset']
                amount = float(pos['totalAmount'])
                
                if amount > 0:
                    current_price = self._get_current_price(asset)
                    
                    if current_price > 0:
                        current_value = amount * current_price
                        avg_price = self._get_average_price(asset) or current_price
                        total_invested = amount * avg_price
                        pnl = current_value - total_invested
                        pnl_percentage = (pnl / total_invested * 100) if total_invested > 0 else 0
                        apr = float(pos.get('latestAnnualPercentageRate', 0)) * 100
                        
                        earn_data.append({
                            'asset': asset,
                            'quantity': amount,
                            'avg_price': avg_price,
                            'current_price': current_price,
                            'current_value': current_value,
                            'total_invested': total_invested,
                            'pnl_percentage': pnl_percentage,
                            'pnl_euro': pnl,
                            'source': 'Simple Earn',
                            'type': 'Locked',
                            'apr': apr
                        })
            
            self.logger.info(f"✅ Simple Earn: {len(earn_data)} posizioni")
            return earn_data
            
        except Exception as e:
            self.logger.error(f"❌ Errore Simple Earn: {e}")
            return []
    
    def _get_current_price(self, asset: str) -> float:
        """Ottiene prezzo attuale per asset"""
        try:
            # Prova USDT
            ticker = self.client.get_symbol_ticker(symbol=f"{asset}USDT")
            price = float(ticker['price'])
            self.logger.debug(f"✅ Prezzo {asset}: {price} USDT")
            return price
        except Exception as e:
            try:
                # Prova BTC
                ticker = self.client.get_symbol_ticker(symbol=f"{asset}BTC")
                btc_price = float(ticker['price'])
                # Converti BTC in USDT
                btc_usdt = self.client.get_symbol_ticker(symbol="BTCUSDT")
                price = btc_price * float(btc_usdt['price'])
                self.logger.debug(f"✅ Prezzo {asset}: {price} USDT (via BTC)")
                return price
            except Exception as e2:
                self.logger.debug(f"⚠️ Prezzo non trovato per {asset}: USDT={e}, BTC={e2}")
                return 0.0
    
    def _get_average_price(self, asset: str) -> float:
        """Calcola prezzo medio di acquisto"""
        try:
            # Per asset LD* (Launchpool), usa prezzo attuale come fallback
            if asset.startswith('LD'):
                current_price = self._get_current_price(asset)
                if current_price > 0:
                    self.logger.debug(f"Asset LD* {asset}: usando prezzo attuale come prezzo medio")
                    return current_price
                return 0.0
            
            # Per asset normali, prova a calcolare dai trade history
            trades = self.client.get_my_trades(symbol=f"{asset}USDT", limit=100)
            if not trades:
                # Prova BTC
                trades = self.client.get_my_trades(symbol=f"{asset}BTC", limit=100)
            
            if trades:
                total_cost = sum(float(t['price']) * float(t['qty']) for t in trades if t['isBuyer'])
                total_quantity = sum(float(t['qty']) for t in trades if t['isBuyer'])
                
                if total_quantity > 0:
                    avg_price = total_cost / total_quantity
                    self.logger.debug(f"Prezzo medio {asset}: {avg_price} USDT (da trade history)")
                    return avg_price
            
            # Fallback: usa prezzo attuale
            current_price = self._get_current_price(asset)
            if current_price > 0:
                self.logger.debug(f"Asset {asset}: usando prezzo attuale come prezzo medio (nessun trade trovato)")
                return current_price
            
            return 0.0
            
        except Exception as e:
            self.logger.debug(f"Impossibile calcolare prezzo medio per {asset}: {e}")
            return 0.0

class GoogleSheetsManager:
    """Gestore per Google Sheets"""
    
    def __init__(self):
        self.logger = logging.getLogger('GoogleSheets')
        self.service = self._create_service()
    
    def _create_service(self):
        """Crea servizio Google Sheets"""
        try:
            # Gestione credenziali
            if Config.GOOGLE_SHEETS_CREDENTIALS:
                credentials_info = json.loads(Config.GOOGLE_SHEETS_CREDENTIALS)
            elif Config.GOOGLE_SHEETS_CREDENTIALS_FILE:
                with open(Config.GOOGLE_SHEETS_CREDENTIALS_FILE, 'r') as f:
                    credentials_info = json.load(f)
            else:
                raise ValueError("Nessuna credenziale Google Sheets trovata")
            
            credentials = Credentials.from_service_account_info(
                credentials_info,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            return build('sheets', 'v4', credentials=credentials)
            
        except Exception as e:
            self.logger.error(f"❌ Errore servizio Google Sheets: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Testa connessione Google Sheets"""
        try:
            self.service.spreadsheets().get(
                spreadsheetId=Config.GOOGLE_SHEET_ID
            ).execute()
            self.logger.info("✅ Connessione Google Sheets OK")
            return True
        except Exception as e:
            self.logger.error(f"❌ Errore Google Sheets: {e}")
            return False
    
    def update_portfolio(self, portfolio_data: List[Dict]):
        """Aggiorna Google Sheets con dati portfolio"""
        try:
            # 1. Pulisci foglio
            self._clear_sheet()
            
            # 2. Scrivi intestazioni
            self._write_headers()
            
            # 3. Scrivi dati
            self._write_data(portfolio_data)
            
            # 4. Aggiungi riepilogo
            self._add_summary(portfolio_data)
            
            self.logger.info("✅ Google Sheets aggiornato")
            
        except Exception as e:
            self.logger.error(f"❌ Errore aggiornamento: {e}")
            raise
    
    def _clear_sheet(self):
        """Pulisce il foglio"""
        range_name = f"{Config.SHEET_NAME}!A2:L1000"
        self.service.spreadsheets().values().clear(
            spreadsheetId=Config.GOOGLE_SHEET_ID,
            range=range_name
        ).execute()
    
    def _write_headers(self):
        """Scrive intestazioni"""
        range_name = f"{Config.SHEET_NAME}!A1:L1"
        body = {'values': [Config.HEADERS]}
        self.service.spreadsheets().values().update(
            spreadsheetId=Config.GOOGLE_SHEET_ID,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
    
    def _write_data(self, portfolio_data: List[Dict]):
        """Scrive dati portfolio"""
        if not portfolio_data:
            return
        
        values = []
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for item in portfolio_data:
            row = [
                item['asset'],
                round(item['quantity'], 8),
                round(item['avg_price'], 2),
                round(item['current_price'], 2),
                round(item['current_value'], 2),
                round(item['total_invested'], 2),
                round(item['pnl_percentage'], 2),
                round(item['pnl_euro'], 2),
                item['source'],
                item['type'],
                round(item['apr'], 2),
                current_time
            ]
            values.append(row)
        
        range_name = f"{Config.SHEET_NAME}!A2:L{len(values)+1}"
        body = {'values': values}
        self.service.spreadsheets().values().update(
            spreadsheetId=Config.GOOGLE_SHEET_ID,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        
        self.logger.info(f"✅ Scritte {len(values)} righe")
    
    def _add_summary(self, portfolio_data: List[Dict]):
        """Aggiunge riga di riepilogo"""
        if not portfolio_data:
            return
        
        total_value = sum(item['current_value'] for item in portfolio_data)
        total_invested = sum(item['total_invested'] for item in portfolio_data)
        total_pnl = sum(item['pnl_euro'] for item in portfolio_data)
        
        summary_row = [
            "TOTALE",
            "",
            "",
            "",
            round(total_value, 2),
            round(total_invested, 2),
            round((total_pnl / total_invested * 100) if total_invested > 0 else 0, 2),
            round(total_pnl, 2),
            f"Spot: {len([i for i in portfolio_data if i['source'] == 'Spot'])} | Earn: {len([i for i in portfolio_data if i['source'] == 'Simple Earn'])}",
            "",
            "",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]
        
        range_name = f"{Config.SHEET_NAME}!A{len(portfolio_data)+3}:L{len(portfolio_data)+3}"
        body = {'values': [summary_row]}
        self.service.spreadsheets().values().update(
            spreadsheetId=Config.GOOGLE_SHEET_ID,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()

def setup_logging():
    """Configura logging"""
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
    logger = logging.getLogger('Main')
    
    try:
        logger.info("🚀 Avvio Crypto Portfolio Tracker")
        logger.info(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. Validazione
        if not Config.validate():
            logger.error("❌ Configurazione non valida")
            return False
        
        # 2. Inizializzazione
        binance = BinanceManager()
        sheets = GoogleSheetsManager()
        
        # 3. Test connessioni
        logger.info("🔍 Test connessioni...")
        if not binance.test_connection():
            return False
        if not sheets.test_connection():
            return False
        
        # 4. Recupero dati
        logger.info("📊 Recupero dati portfolio...")
        portfolio_data = binance.get_portfolio_data()
        
        if not portfolio_data:
            logger.warning("⚠️ Nessun dato portfolio trovato")
            return False
        
        # 5. Aggiornamento Google Sheets
        logger.info("📝 Aggiornamento Google Sheets...")
        sheets.update_portfolio(portfolio_data)
        
        # 6. Risultati
        total_value = sum(item['current_value'] for item in portfolio_data)
        total_invested = sum(item['total_invested'] for item in portfolio_data)
        total_pnl = sum(item['pnl_euro'] for item in portfolio_data)
        
        spot_count = len([i for i in portfolio_data if i['source'] == 'Spot'])
        earn_count = len([i for i in portfolio_data if i['source'] == 'Simple Earn'])
        
        logger.info("🎉 Aggiornamento completato!")
        logger.info(f"💰 Valore totale: €{total_value:,.2f}")
        logger.info(f"💸 Investito totale: €{total_invested:,.2f}")
        logger.info(f"📈 PnL totale: €{total_pnl:,.2f}")
        logger.info(f"📊 Asset Spot: {spot_count}")
        logger.info(f"📊 Asset Simple Earn: {earn_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 