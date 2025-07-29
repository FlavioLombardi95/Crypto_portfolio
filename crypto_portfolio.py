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
            
            # 3. Filtra asset con valore >= 1€
            filtered_data = [item for item in portfolio_data if item['current_value'] >= 1.0]
            
            # 4. Ordina per valore
            filtered_data.sort(key=lambda x: x['current_value'], reverse=True)
            
            self.logger.info(f"✅ Portfolio filtrato: {len(filtered_data)} asset (valore >= 1€)")
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
                asset = balance['asset']
                
                # Ignora asset LD* (Launchpool)
                if asset.startswith('LD'):
                    continue
                
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total > 0:
                    current_price = self._get_current_price(asset)
                    
                    if current_price > 0:
                        current_value = total * current_price
                        # Prezzo medio lasciato vuoto per inserimento manuale
                        avg_price = 0.0
                        total_invested = 0.0  # Calcolato dall'utente
                        pnl = 0.0  # Calcolato dall'utente
                        pnl_percentage = 0.0  # Calcolato dall'utente
                        
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
            
            # Lista asset da controllare (basata sui test precedenti)
            assets_to_check = ['ARB', 'BNB', 'BTC', 'C', 'ERA', 'ETH', 'HAEDAL', 'HOME', 'HUMA', 'HYPER', 'SOL', 'TAO', 'OP', 'ONDO']
            
            # Controlla ogni asset individualmente
            for asset in assets_to_check:
                try:
                    # Flexible positions per asset specifico
                    flexible = self.client.get_simple_earn_flexible_product_position(asset=asset)
                    
                    if flexible and flexible.get('rows'):
                        for pos in flexible['rows']:
                            amount = float(pos['totalAmount'])
                            
                            if amount > 0:
                                current_price = self._get_current_price(asset)
                                
                                if current_price > 0:
                                    current_value = amount * current_price
                                    # Prezzo medio lasciato vuoto per inserimento manuale
                                    avg_price = 0.0
                                    total_invested = 0.0  # Calcolato dall'utente
                                    pnl = 0.0  # Calcolato dall'utente
                                    pnl_percentage = 0.0  # Calcolato dall'utente
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
                    
                    # Locked positions per asset specifico
                    locked = self.client.get_simple_earn_locked_product_position(asset=asset)
                    
                    if locked and locked.get('rows'):
                        for pos in locked['rows']:
                            amount = float(pos['totalAmount'])
                            
                            if amount > 0:
                                current_price = self._get_current_price(asset)
                                
                                if current_price > 0:
                                    current_value = amount * current_price
                                    # Prezzo medio lasciato vuoto per inserimento manuale
                                    avg_price = 0.0
                                    total_invested = 0.0  # Calcolato dall'utente
                                    pnl = 0.0  # Calcolato dall'utente
                                    pnl_percentage = 0.0  # Calcolato dall'utente
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
                                    
                except Exception as e:
                    self.logger.debug(f"Error processing {asset}: {e}")
                    continue
            
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
        """Calcola prezzo medio di acquisto (limitazione: non corrisponde al costo medio Binance)"""
        try:
            # Prova a calcolare dai trade history (limitato ai trade disponibili via API)
            trades = self.client.get_my_trades(symbol=f"{asset}USDT", limit=100)
            if not trades:
                # Prova BTC
                trades = self.client.get_my_trades(symbol=f"{asset}BTC", limit=100)
            
            if trades:
                buy_trades = [t for t in trades if t['isBuyer']]
                if buy_trades:
                    total_cost = sum(float(t['quoteQty']) for t in buy_trades)
                    total_quantity = sum(float(t['qty']) for t in buy_trades)
                    
                    if total_quantity > 0:
                        avg_price = total_cost / total_quantity
                        self.logger.debug(f"Prezzo medio {asset}: {avg_price} USDT (da trade history limitato)")
                        return avg_price
            
            # Fallback: usa prezzo attuale (non è il costo medio reale)
            current_price = self._get_current_price(asset)
            if current_price > 0:
                self.logger.debug(f"Asset {asset}: usando prezzo attuale (costo medio non disponibile via API)")
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
            
            # 5. Applica formattazione
            self._apply_formatting(len(portfolio_data))
            
            self.logger.info("✅ Google Sheets aggiornato")
            
        except Exception as e:
            self.logger.error(f"❌ Errore aggiornamento: {e}")
            raise
    
    def _clear_sheet(self):
        """Pulisce il foglio (escludendo colonna Prezzo Medio)"""
        # Pulisci solo le colonne che vengono sovrascritte
        # A, B, D, E, F, G, H, I, J, K, L (escludendo C - Prezzo Medio)
        ranges_to_clear = [
            f"{Config.SHEET_NAME}!A2:A1000",  # Asset
            f"{Config.SHEET_NAME}!B2:B1000",  # Quantità
            f"{Config.SHEET_NAME}!D2:L1000"   # Tutte le altre colonne (D-L)
        ]
        
        for range_name in ranges_to_clear:
            self.service.spreadsheets().values().clear(
                spreadsheetId=Config.GOOGLE_SHEET_ID,
                range=range_name
            ).execute()
        
        self.logger.info("🧹 Foglio pulito (colonna C preservata)")
    
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
        """Scrive dati portfolio preservando prezzi medi esistenti"""
        if not portfolio_data:
            return
        
        # 1. Leggi prezzi medi esistenti
        existing_prices = self._get_existing_prices()
        
        # 2. Scrivi colonne A, B, D-L (escludendo C)
        values_ab = []  # Colonne A-B
        values_dl = []  # Colonne D-L
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for i, item in enumerate(portfolio_data, start=1):
            asset = item['asset']
            # Usa prezzo medio esistente per indice di riga o lascia vuoto
            existing_price = existing_prices.get(f"row_{i}", "")
            
            # Calcola automaticamente se c'è un prezzo medio
            total_invested = ""
            pnl_percentage = ""
            pnl_usdt = ""
            
            if existing_price and existing_price.strip():
                try:
                    # Converti formato europeo (virgola) in formato americano (punto)
                    price_str = existing_price.replace(',', '.')
                    avg_price = float(price_str)
                    quantity = item['quantity']
                    current_value = item['current_value']
                    
                    total_invested = round(quantity * avg_price, 2)
                    pnl_usdt = round(current_value - total_invested, 2)
                    # PnL % già in percentuale, non moltiplicare per 100 (Google Sheets lo fa automaticamente)
                    pnl_percentage = round((pnl_usdt / total_invested), 4) if total_invested > 0 else 0
                    
                    self.logger.debug(f"💰 {asset}: Calcoli automatici completati")
                    
                except (ValueError, TypeError) as e:
                    # Se il prezzo medio non è un numero valido, lascia vuoto
                    self.logger.warning(f"⚠️ {asset}: Errore calcolo - {e}")
            else:
                self.logger.debug(f"📝 {asset}: Nessun prezzo medio trovato")
            
            # APR già in percentuale, non moltiplicare per 100 (Google Sheets lo fa automaticamente)
            apr_value = round(item['apr'] / 100, 4)
            
            # Colonna A-B (Asset, Quantità)
            row_ab = [
                item['asset'],                    # A - Asset
                round(item['quantity'], 8)        # B - Quantità
            ]
            values_ab.append(row_ab)
            
            # Colonne D-L (escludendo C)
            row_dl = [
                round(item['current_price'], 2),  # D - Prezzo Attuale
                round(item['current_value'], 2),  # E - Valore Attuale
                total_invested,                   # F - Investito Totale (calcolato automaticamente)
                pnl_percentage,                   # G - PnL % (calcolato automaticamente)
                pnl_usdt,                         # H - PnL USDT (calcolato automaticamente)
                item['source'],                   # I - Fonte
                item['type'],                     # J - Tipo
                apr_value,                        # K - APR % (4 decimali per precisione)
                current_time                      # L - Ultimo Aggiornamento
            ]
            values_dl.append(row_dl)
        
        # 3. Scrivi colonne A-B
        range_ab = f"{Config.SHEET_NAME}!A2:B{len(values_ab)+1}"
        body_ab = {'values': values_ab}
        self.service.spreadsheets().values().update(
            spreadsheetId=Config.GOOGLE_SHEET_ID,
            range=range_ab,
            valueInputOption='RAW',
            body=body_ab
        ).execute()
        
        # 4. Scrivi colonne D-L
        range_dl = f"{Config.SHEET_NAME}!D2:L{len(values_dl)+1}"
        body_dl = {'values': values_dl}
        self.service.spreadsheets().values().update(
            spreadsheetId=Config.GOOGLE_SHEET_ID,
            range=range_dl,
            valueInputOption='RAW',
            body=body_dl
        ).execute()
        
        self.logger.info(f"✅ Scritte {len(values_ab)} righe (colonna C preservata)")
    
    def _add_summary(self, portfolio_data: List[Dict]):
        """Aggiunge riga di riepilogo"""
        if not portfolio_data:
            return
        
        # Calcola totali dai dati del portfolio
        total_value = sum(item['current_value'] for item in portfolio_data)
        
        # Calcola totali investiti e PnL dai prezzi medi esistenti
        existing_prices = self._get_existing_prices()
        total_invested = 0
        total_pnl = 0
        
        for i, item in enumerate(portfolio_data, start=1):
            existing_price = existing_prices.get(f"row_{i}", "")
            if existing_price and existing_price.strip():
                try:
                    # Converti formato europeo (virgola) in formato americano (punto)
                    price_str = existing_price.replace(',', '.')
                    avg_price = float(price_str)
                    quantity = item['quantity']
                    current_value = item['current_value']
                    
                    invested = quantity * avg_price
                    pnl = current_value - invested
                    
                    total_invested += invested
                    total_pnl += pnl
                    
                except (ValueError, TypeError):
                    pass
        
        # Calcola PnL % totale
        total_pnl_percentage = (total_pnl / total_invested) if total_invested > 0 else 0
        
        summary_row = [
            "TOTALE",
            "",
            "",
            "",
            round(total_value, 2),
            round(total_invested, 2),
            round(total_pnl_percentage, 4),  # Non moltiplicare per 100 (Google Sheets lo fa)
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
    
    def _get_existing_prices(self) -> Dict[str, str]:
        """Legge prezzi medi esistenti dal foglio"""
        try:
            # Leggi solo colonna C (Prezzo Medio) esistente
            range_name = f"{Config.SHEET_NAME}!C:C"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=Config.GOOGLE_SHEET_ID,
                range=range_name
            ).execute()
            
            existing_prices = {}
            values = result.get('values', [])
            
            # Salta header (riga 1) e leggi prezzi per indice
            for i, row in enumerate(values[1:], start=1):
                if row and len(row) > 0:
                    price = row[0]  # Colonna C - Prezzo Medio
                    
                    # Salva solo se il prezzo non è vuoto
                    if price and price.strip() and price != "":
                        # Usa l'indice della riga come chiave temporanea
                        existing_prices[f"row_{i}"] = price
            
            self.logger.info(f"📖 Prezzi medi esistenti trovati: {len(existing_prices)}")
            return existing_prices
            
        except Exception as e:
            self.logger.error(f"❌ Errore lettura prezzi esistenti: {e}")
            return {}
    
    def _apply_formatting(self, data_rows: int):
        """Applica formattazione automatica alle colonne"""
        try:
            # Calcola range dati (escludendo header e summary)
            data_range = f"{Config.SHEET_NAME}!A2:L{data_rows+1}"
            summary_range = f"{Config.SHEET_NAME}!A{data_rows+3}:L{data_rows+3}"
            
            # 1. Formattazione header in bold (riga 1)
            self._format_header_bold()
            
            # 2. Formattazione riga totali in bold
            self._format_summary_bold(data_rows)
            
            # 3. Formattazione condizionale PnL % (colonna G)
            self._format_conditional_pnl(data_rows)
            
            # Formattazione per colonne USDT ($)
            usdt_columns = ['D', 'E', 'F', 'H']  # Prezzo Attuale, Valore Attuale, Investito, PnL USDT
            
            for col in usdt_columns:
                # Formatta colonne dati
                data_col_range = f"{Config.SHEET_NAME}!{col}2:{col}{data_rows+1}"
                self._format_currency(data_col_range)
                
                # Formatta colonna summary
                summary_col_range = f"{Config.SHEET_NAME}!{col}{data_rows+3}:{col}{data_rows+3}"
                self._format_currency(summary_col_range)
            
            # Formattazione per colonne percentuali (%)
            percent_columns = ['K']  # APR % (PnL % gestito separatamente)
            
            for col in percent_columns:
                # Formatta colonne dati
                data_col_range = f"{Config.SHEET_NAME}!{col}2:{col}{data_rows+1}"
                self._format_percentage(data_col_range)
                
                # Formatta colonna summary
                summary_col_range = f"{Config.SHEET_NAME}!{col}{data_rows+3}:{col}{data_rows+3}"
                self._format_percentage(summary_col_range)
            
            # Formattazione quantità (8 decimali)
            quantity_range = f"{Config.SHEET_NAME}!B2:B{data_rows+1}"
            self._format_number(quantity_range, 8)
            
            # Formattazione prezzo medio (valuta USD)
            avg_price_range = f"{Config.SHEET_NAME}!C2:C{data_rows+1}"
            self._format_currency(avg_price_range)
            
            self.logger.info("✅ Formattazione applicata")
            
        except Exception as e:
            self.logger.error(f"❌ Errore formattazione: {e}")
    
    def _format_currency(self, range_name: str):
        """Formatta come valuta USD"""
        # Parsing del range (es. "Portfolio!D2:D7")
        sheet_name, cell_range = range_name.split('!')
        if ':' in cell_range:
            start_cell, end_cell = cell_range.split(':')
        else:
            start_cell = end_cell = cell_range
        
        # Estrai colonna e riga
        start_col = ''.join(filter(str.isalpha, start_cell))
        start_row = int(''.join(filter(str.isdigit, start_cell)))
        end_col = ''.join(filter(str.isalpha, end_cell))
        end_row = int(''.join(filter(str.isdigit, end_cell)))
        
        request = {
            'repeatCell': {
                'range': {
                    'sheetId': 0,  # Primo foglio
                    'startRowIndex': start_row - 1,
                    'endRowIndex': end_row,
                    'startColumnIndex': ord(start_col) - ord('A'),
                    'endColumnIndex': ord(end_col) - ord('A') + 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'numberFormat': {
                            'type': 'CURRENCY',
                            'pattern': '$#,##0.00'
                        }
                    }
                },
                'fields': 'userEnteredFormat.numberFormat'
            }
        }
        
        self.service.spreadsheets().batchUpdate(
            spreadsheetId=Config.GOOGLE_SHEET_ID,
            body={'requests': [request]}
        ).execute()
    
    def _format_percentage(self, range_name: str):
        """Formatta come percentuale"""
        # Parsing del range (es. "Portfolio!G2:G7")
        sheet_name, cell_range = range_name.split('!')
        if ':' in cell_range:
            start_cell, end_cell = cell_range.split(':')
        else:
            start_cell = end_cell = cell_range
        
        # Estrai colonna e riga
        start_col = ''.join(filter(str.isalpha, start_cell))
        start_row = int(''.join(filter(str.isdigit, start_cell)))
        end_col = ''.join(filter(str.isalpha, end_cell))
        end_row = int(''.join(filter(str.isdigit, end_cell)))
        
        request = {
            'repeatCell': {
                'range': {
                    'sheetId': 0,
                    'startRowIndex': start_row - 1,
                    'endRowIndex': end_row,
                    'startColumnIndex': ord(start_col) - ord('A'),
                    'endColumnIndex': ord(end_col) - ord('A') + 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'numberFormat': {
                            'type': 'PERCENT',
                            'pattern': '0.00%'
                        }
                    }
                },
                'fields': 'userEnteredFormat.numberFormat'
            }
        }
        
        self.service.spreadsheets().batchUpdate(
            spreadsheetId=Config.GOOGLE_SHEET_ID,
            body={'requests': [request]}
        ).execute()
    
    def _format_header_bold(self):
        """Formatta header (riga 1) in bold"""
        request = {
            'repeatCell': {
                'range': {
                    'sheetId': 0,
                    'startRowIndex': 0,
                    'endRowIndex': 1,
                    'startColumnIndex': 0,
                    'endColumnIndex': 12  # Colonne A-L
                },
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {
                            'bold': True
                        }
                    }
                },
                'fields': 'userEnteredFormat.textFormat.bold'
            }
        }
        
        self.service.spreadsheets().batchUpdate(
            spreadsheetId=Config.GOOGLE_SHEET_ID,
            body={'requests': [request]}
        ).execute()
    
    def _format_summary_bold(self, data_rows: int):
        """Formatta riga totali in bold"""
        summary_row = data_rows + 3  # Riga dopo i dati + 1 riga vuota
        
        request = {
            'repeatCell': {
                'range': {
                    'sheetId': 0,
                    'startRowIndex': summary_row - 1,
                    'endRowIndex': summary_row,
                    'startColumnIndex': 0,
                    'endColumnIndex': 12  # Colonne A-L
                },
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {
                            'bold': True
                        }
                    }
                },
                'fields': 'userEnteredFormat.textFormat.bold'
            }
        }
        
        self.service.spreadsheets().batchUpdate(
            spreadsheetId=Config.GOOGLE_SHEET_ID,
            body={'requests': [request]}
        ).execute()
    
    def _format_conditional_pnl(self, data_rows: int):
        """Applica formattazione condizionale alla colonna PnL % (G)"""
        # Range per la colonna PnL % (escludendo header e summary)
        pnl_range = f"{Config.SHEET_NAME}!G2:G{data_rows+1}"
        
        # Formattazione percentuale base
        self._format_percentage(pnl_range)
        
        # Formattazione condizionale: rosso per perdite, verde per profitti
        # Scala da -100% a 100%
        request = {
            'addConditionalFormatRule': {
                'rule': {
                    'ranges': [{
                        'sheetId': 0,
                        'startRowIndex': 1,  # Riga 2 (dopo header)
                        'endRowIndex': data_rows + 1,
                        'startColumnIndex': 6,  # Colonna G
                        'endColumnIndex': 7
                    }],
                    'gradientRule': {
                        'minpoint': {
                            'color': {
                                'red': 1.0,    # Rosso
                                'green': 0.0,
                                'blue': 0.0
                            },
                            'type': 'NUMBER',
                            'value': '-1'  # -100%
                        },
                        'midpoint': {
                            'color': {
                                'red': 1.0,    # Bianco
                                'green': 1.0,
                                'blue': 1.0
                            },
                            'type': 'NUMBER',
                            'value': '0'   # 0%
                        },
                        'maxpoint': {
                            'color': {
                                'red': 0.0,    # Verde
                                'green': 1.0,
                                'blue': 0.0
                            },
                            'type': 'NUMBER',
                            'value': '1'   # 100%
                        }
                    }
                }
            }
        }
        
        self.service.spreadsheets().batchUpdate(
            spreadsheetId=Config.GOOGLE_SHEET_ID,
            body={'requests': [request]}
        ).execute()
    
    def _format_number(self, range_name: str, decimals: int):
        """Formatta come numero con decimali specificati"""
        # Parsing del range (es. "Portfolio!B2:B7")
        sheet_name, cell_range = range_name.split('!')
        if ':' in cell_range:
            start_cell, end_cell = cell_range.split(':')
        else:
            start_cell = end_cell = cell_range
        
        # Estrai colonna e riga
        start_col = ''.join(filter(str.isalpha, start_cell))
        start_row = int(''.join(filter(str.isdigit, start_cell)))
        end_col = ''.join(filter(str.isalpha, end_cell))
        end_row = int(''.join(filter(str.isdigit, end_cell)))
        
        pattern = f"#,##0.{'0' * decimals}"
        request = {
            'repeatCell': {
                'range': {
                    'sheetId': 0,
                    'startRowIndex': start_row - 1,
                    'endRowIndex': end_row,
                    'startColumnIndex': ord(start_col) - ord('A'),
                    'endColumnIndex': ord(end_col) - ord('A') + 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'numberFormat': {
                            'type': 'NUMBER',
                            'pattern': pattern
                        }
                    }
                },
                'fields': 'userEnteredFormat.numberFormat'
            }
        }
        
        self.service.spreadsheets().batchUpdate(
            spreadsheetId=Config.GOOGLE_SHEET_ID,
            body={'requests': [request]}
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