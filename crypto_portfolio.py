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
    OVERVIEW_SHEET_NAME = 'Overview'
    CHART_SHEET_NAME = 'Grafico'
    START_ROW = 2
    
    # Headers
    HEADERS = [
        'Asset', 'Quantità', 'Prezzo Medio (USDT)', 'Prezzo Attuale (USDT)',
        'Valore Attuale (USDT)', 'Investito Totale (USDT)', 'PnL %', 'PnL USDT',
        'Fonte', 'Tipo', 'APR %', 'Ultimo Aggiornamento'
    ]
    
    # Overview Headers
    OVERVIEW_HEADERS = [
        'Data Ultimo Aggiornamento', 'Valore Attuale Portfolio (USDT)', 
        'Investito Totale (USDT)', 'PnL USDT Totale (USDT)', 'PnL %'
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
        self.logger = logging.getLogger('Binance')
        self.client = Client(Config.BINANCE_API_KEY, Config.BINANCE_SECRET_KEY)
    
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
        """Recupera dati portafoglio completo (Spot + Simple Earn) con validazione robusta"""
        try:
            portfolio_data = []
            
            # 1. Dati Spot
            spot_data = self._get_spot_data()
            portfolio_data.extend(spot_data)
            
            # 2. Dati Simple Earn
            earn_data = self._get_earn_data()
            portfolio_data.extend(earn_data)
            
            self.logger.info(f"📊 Asset totali trovati: {len(portfolio_data)}")
            
            # 3. Validazione e pulizia dati
            valid_data = []
            for item in portfolio_data:
                try:
                    # Verifica che tutti i campi necessari siano presenti
                    required_fields = ['asset', 'quantity', 'current_price', 'current_value']
                    if all(field in item and item[field] is not None for field in required_fields):
                        # Verifica che i valori siano numerici e positivi
                        if (isinstance(item['quantity'], (int, float)) and item['quantity'] > 0 and
                            isinstance(item['current_price'], (int, float)) and item['current_price'] > 0 and
                            isinstance(item['current_value'], (int, float)) and item['current_value'] > 0):
                            valid_data.append(item)
                        else:
                            self.logger.warning(f"⚠️ Dati non validi per {item.get('asset', 'Unknown')}: quantità={item.get('quantity')}, prezzo={item.get('current_price')}, valore={item.get('current_value')}")
                    else:
                        self.logger.warning(f"⚠️ Campi mancanti per asset: {item.get('asset', 'Unknown')}")
                except Exception as e:
                    self.logger.error(f"❌ Errore validazione asset {item.get('asset', 'Unknown')}: {e}")
                    continue
            
            # 4. Filtra asset con valore >= 1€
            filtered_data = [item for item in valid_data if item['current_value'] >= 1.0]
            
            # 5. Ordina per valore
            filtered_data.sort(key=lambda x: x['current_value'], reverse=True)
            
            # 6. Log dettagliato
            self.logger.info(f"📊 Asset validi: {len(valid_data)}")
            self.logger.info(f"✅ Portfolio filtrato: {len(filtered_data)} asset (valore >= 1€)")
            
            # 7. Log asset trovati per debug
            if filtered_data:
                asset_list = [item['asset'] for item in filtered_data]
                self.logger.info(f"📋 Asset nel portfolio: {', '.join(asset_list)}")
            
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
        """Recupera dati Simple Earn usando API REST diretta con retry e fallback robusti"""
        try:
            earn_data = []
            
            self.logger.info("🔍 Recupero Simple Earn con API REST diretta...")
            
            # Strategia 1: Recupera tutte le posizioni (flexible + locked)
            all_positions = self._get_all_simple_earn_positions()
            if all_positions:
                earn_data.extend(all_positions)
                self.logger.info(f"✅ Posizioni totali recuperate: {len(all_positions)}")
            
            # Strategia 2: Verifica asset noti e cerca quelli mancanti
            known_assets = ['ARB', 'BNB', 'BTC', 'C', 'ERA', 'ETH', 'HAEDAL', 'HOME', 'HUMA', 'HYPER', 'OP', 'SOL', 'ONDO', 'TAO']
            found_assets = [item['asset'] for item in earn_data]
            missing_assets = [asset for asset in known_assets if asset not in found_assets]
            
            if missing_assets:
                self.logger.info(f"🔍 Asset mancanti: {missing_assets}")
                # Strategia 3: Ricerca specifica per asset mancanti
                for asset in missing_assets:
                    self.logger.info(f"🔍 Ricerca specifica per: {asset}")
                    specific_positions = self._get_simple_earn_asset_positions(asset)
                    if specific_positions:
                        earn_data.extend(specific_positions)
                        self.logger.info(f"✅ Trovato {asset} in ricerca specifica")
                    else:
                        self.logger.warning(f"⚠️ Asset {asset} non trovato in Simple Earn")
            
            # Rimuovi duplicati (se presenti)
            unique_earn_data = []
            seen_assets = set()
            for item in earn_data:
                if item['asset'] not in seen_assets:
                    unique_earn_data.append(item)
                    seen_assets.add(item['asset'])
            
            self.logger.info(f"✅ Simple Earn: {len(unique_earn_data)} posizioni uniche")
            return unique_earn_data
            
        except Exception as e:
            self.logger.error(f"❌ Errore Simple Earn: {e}")
            return []
    
    def _get_all_simple_earn_positions(self) -> List[Dict]:
        """Recupera tutte le posizioni Simple Earn (flexible + locked) con retry logic"""
        try:
            import time
            import hmac
            import hashlib
            import requests
            
            all_positions = []
            
            # Lista di endpoint da provare
            endpoints = [
                ('FLEXIBLE', 'https://api.binance.com/sapi/v1/simple-earn/flexible/position'),
                ('LOCKED', 'https://api.binance.com/sapi/v1/simple-earn/locked/position')
            ]
            
            for product_type, url in endpoints:
                try:
                    # Retry logic (3 tentativi)
                    for attempt in range(3):
                        try:
                            # Parametri per la richiesta
                            timestamp = int(time.time() * 1000)
                            params = {
                                'timestamp': timestamp
                            }
                            
                            # Crea signature
                            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
                            signature = hmac.new(
                                Config.BINANCE_SECRET_KEY.encode('utf-8'),
                                query_string.encode('utf-8'),
                                hashlib.sha256
                            ).hexdigest()
                            
                            headers = {
                                'X-MBX-APIKEY': Config.BINANCE_API_KEY
                            }
                            
                            # Aggiungi signature ai parametri
                            params['signature'] = signature
                            
                            # Fai la richiesta con timeout
                            response = requests.get(url, headers=headers, params=params, timeout=10)
                            
                            if response.status_code == 200:
                                data = response.json()
                                positions = []
                                
                                if 'rows' in data and data['rows']:
                                    for pos in data['rows']:
                                        asset = pos['asset']
                                        amount = float(pos['totalAmount'])
                                        
                                        if amount > 0:
                                            current_price = self._get_current_price(asset)
                                            
                                            if current_price > 0:
                                                current_value = amount * current_price
                                                avg_price = 0.0
                                                total_invested = 0.0
                                                pnl = 0.0
                                                pnl_percentage = 0.0
                                                apr = float(pos.get('latestAnnualPercentageRate', 0)) * 100
                                                
                                                positions.append({
                                                    'asset': asset,
                                                    'quantity': amount,
                                                    'avg_price': avg_price,
                                                    'current_price': current_price,
                                                    'current_value': current_value,
                                                    'total_invested': total_invested,
                                                    'pnl_percentage': pnl_percentage,
                                                    'pnl_euro': pnl,
                                                    'source': 'Simple Earn',
                                                    'type': product_type.title(),
                                                    'apr': apr
                                                })
                                                
                                                self.logger.info(f"💰 {asset} ({product_type}): {amount} @ {current_price} = {current_value:.2f} USDT")
                                
                                all_positions.extend(positions)
                                self.logger.info(f"✅ {product_type} positions: {len(positions)} posizioni")
                                break  # Successo, esci dal retry loop
                                
                            else:
                                self.logger.warning(f"⚠️ Tentativo {attempt + 1} fallito per {product_type}: {response.status_code}")
                                if attempt < 2:  # Non è l'ultimo tentativo
                                    time.sleep(1)  # Pausa prima del retry
                                    
                        except requests.exceptions.RequestException as e:
                            self.logger.warning(f"⚠️ Errore di rete per {product_type} (tentativo {attempt + 1}): {e}")
                            if attempt < 2:
                                time.sleep(1)
                            continue
                            
                except Exception as e:
                    self.logger.error(f"❌ Errore recupero {product_type}: {e}")
                    continue
            
            return all_positions
            
        except Exception as e:
            self.logger.error(f"❌ Errore recupero tutte le posizioni: {e}")
            return []
    
    def _get_simple_earn_positions(self, product_type: str) -> List[Dict]:
        """Recupera posizioni Simple Earn per tipo specifico"""
        try:
            import time
            import hmac
            import hashlib
            import requests
            
            # Parametri per la richiesta
            timestamp = int(time.time() * 1000)
            params = {
                'timestamp': timestamp
            }
            
            # Crea signature
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            signature = hmac.new(
                Config.BINANCE_SECRET_KEY.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # URL e headers
            url = f"https://api.binance.com/sapi/v1/simple-earn/flexible/position"
            if product_type == 'LOCKED':
                url = f"https://api.binance.com/sapi/v1/simple-earn/locked/position"
            
            headers = {
                'X-MBX-APIKEY': Config.BINANCE_API_KEY
            }
            
            # Aggiungi signature ai parametri
            params['signature'] = signature
            
            # Fai la richiesta
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                positions = []
                
                if 'rows' in data and data['rows']:
                    for pos in data['rows']:
                        asset = pos['asset']
                        amount = float(pos['totalAmount'])
                        
                        if amount > 0:
                            current_price = self._get_current_price(asset)
                            
                            if current_price > 0:
                                current_value = amount * current_price
                                avg_price = 0.0
                                total_invested = 0.0
                                pnl = 0.0
                                pnl_percentage = 0.0
                                apr = float(pos.get('latestAnnualPercentageRate', 0)) * 100
                                
                                positions.append({
                                    'asset': asset,
                                    'quantity': amount,
                                    'avg_price': avg_price,
                                    'current_price': current_price,
                                    'current_value': current_value,
                                    'total_invested': total_invested,
                                    'pnl_percentage': pnl_percentage,
                                    'pnl_euro': pnl,
                                    'source': 'Simple Earn',
                                    'type': product_type.title(),
                                    'apr': apr
                                })
                                
                                self.logger.info(f"💰 {asset} ({product_type}): {amount} @ {current_price} = {current_value:.2f} USDT")
                
                return positions
            else:
                self.logger.error(f"❌ Errore API Simple Earn {product_type}: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            self.logger.error(f"❌ Errore recupero posizioni {product_type}: {e}")
            return []
    
    def _get_simple_earn_asset_positions(self, asset: str) -> List[Dict]:
        """Recupera posizioni Simple Earn per asset specifico con retry logic"""
        try:
            import time
            import hmac
            import hashlib
            import requests
            
            positions = []
            
            # Lista di endpoint da provare per questo asset
            endpoints = [
                ('FLEXIBLE', 'https://api.binance.com/sapi/v1/simple-earn/flexible/position'),
                ('LOCKED', 'https://api.binance.com/sapi/v1/simple-earn/locked/position')
            ]
            
            for product_type, url in endpoints:
                try:
                    # Retry logic (2 tentativi per asset specifico)
                    for attempt in range(2):
                        try:
                            timestamp = int(time.time() * 1000)
                            params = {
                                'asset': asset,
                                'timestamp': timestamp
                            }
                            
                            # Crea signature
                            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
                            signature = hmac.new(
                                Config.BINANCE_SECRET_KEY.encode('utf-8'),
                                query_string.encode('utf-8'),
                                hashlib.sha256
                            ).hexdigest()
                            
                            headers = {'X-MBX-APIKEY': Config.BINANCE_API_KEY}
                            params['signature'] = signature
                            
                            # Fai la richiesta con timeout
                            response = requests.get(url, headers=headers, params=params, timeout=10)
                            
                            if response.status_code == 200:
                                data = response.json()
                                if 'rows' in data and data['rows']:
                                    for pos in data['rows']:
                                        amount = float(pos['totalAmount'])
                                        if amount > 0:
                                            current_price = self._get_current_price(asset)
                                            if current_price > 0:
                                                current_value = amount * current_price
                                                apr = float(pos.get('latestAnnualPercentageRate', 0)) * 100
                                                
                                                positions.append({
                                                    'asset': asset,
                                                    'quantity': amount,
                                                    'avg_price': 0.0,
                                                    'current_price': current_price,
                                                    'current_value': current_value,
                                                    'total_invested': 0.0,
                                                    'pnl_percentage': 0.0,
                                                    'pnl_euro': 0.0,
                                                    'source': 'Simple Earn',
                                                    'type': product_type.title(),
                                                    'apr': apr
                                                })
                                                self.logger.info(f"💰 {asset} ({product_type} specifico): {amount} @ {current_price} = {current_value:.2f} USDT")
                                break  # Successo, esci dal retry loop
                                
                            else:
                                if attempt < 1:  # Non è l'ultimo tentativo
                                    time.sleep(0.5)  # Pausa breve
                                    
                        except requests.exceptions.RequestException as e:
                            if attempt < 1:
                                time.sleep(0.5)
                            continue
                            
                except Exception as e:
                    self.logger.debug(f"⚠️ Errore per {asset} ({product_type}): {e}")
                    continue
            
            return positions
            
        except Exception as e:
            self.logger.error(f"❌ Errore recupero posizioni specifiche per {asset}: {e}")
            return []
            
        except Exception as e:
            self.logger.error(f"❌ Errore Simple Earn: {e}")
            return []
    
    def _get_current_price(self, asset: str) -> float:
        """Ottiene prezzo attuale per asset con cache"""
        try:
            import time
            
            # Cache dei prezzi per ridurre chiamate API
            if not hasattr(self, '_price_cache'):
                self._price_cache = {}
            
            # Controlla se il prezzo è in cache e non è troppo vecchio (5 minuti)
            current_time = time.time()
            if asset in self._price_cache:
                cached_price, cached_time = self._price_cache[asset]
                if current_time - cached_time < 300:  # 5 minuti
                    return cached_price
            
            # Recupera nuovo prezzo
            try:
                # Prova USDT
                ticker = self.client.get_symbol_ticker(symbol=f"{asset}USDT")
                price = float(ticker['price'])
                self.logger.debug(f"✅ Prezzo {asset}: {price} USDT")
            except Exception as e:
                try:
                    # Prova BTC
                    ticker = self.client.get_symbol_ticker(symbol=f"{asset}BTC")
                    btc_price = float(ticker['price'])
                    # Converti BTC in USDT
                    btc_usdt = self.client.get_symbol_ticker(symbol="BTCUSDT")
                    price = btc_price * float(btc_usdt['price'])
                    self.logger.debug(f"✅ Prezzo {asset}: {price} USDT (via BTC)")
                except Exception as e2:
                    self.logger.debug(f"⚠️ Prezzo non trovato per {asset}: USDT={e}, BTC={e2}")
                    return 0.0
            
            # Salva in cache
            self._price_cache[asset] = (price, current_time)
            return price
            
        except Exception as e:
            self.logger.error(f"❌ Errore recupero prezzo {asset}: {e}")
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
            
            # 6. Aggiorna Overview
            self._update_overview(portfolio_data)
            
            # 7. Aggiorna Grafico
            self._update_chart()
            
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
        """Scrive intestazioni (escludendo colonna C)"""
        # Scrivi solo colonne A-B e D-L (escludendo C)
        headers_ab = [Config.HEADERS[0], Config.HEADERS[1]]  # A-B
        headers_dl = Config.HEADERS[3:]  # D-L (escludendo C)
        
        # Scrivi colonne A-B
        range_ab = f"{Config.SHEET_NAME}!A1:B1"
        body_ab = {'values': [headers_ab]}
        self.service.spreadsheets().values().update(
            spreadsheetId=Config.GOOGLE_SHEET_ID,
            range=range_ab,
            valueInputOption='RAW',
            body=body_ab
        ).execute()
        
        # Scrivi colonne D-L
        range_dl = f"{Config.SHEET_NAME}!D1:L1"
        body_dl = {'values': [headers_dl]}
        self.service.spreadsheets().values().update(
            spreadsheetId=Config.GOOGLE_SHEET_ID,
            range=range_dl,
            valueInputOption='RAW',
            body=body_dl
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
                    # Pulisci il prezzo da simboli di valuta e spazi
                    price_str = existing_price.replace('$', '').replace('€', '').replace(' ', '').strip()
                    # Converti formato europeo (virgola) in formato americano (punto)
                    price_str = price_str.replace(',', '.')
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
                    # Pulisci il prezzo da simboli di valuta e spazi
                    price_str = existing_price.replace('$', '').replace('€', '').replace(' ', '').strip()
                    # Converti formato europeo (virgola) in formato americano (punto)
                    price_str = price_str.replace(',', '.')
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
        """Formatta header (riga 1) in bold (escludendo colonna C)"""
        try:
            # Formatta colonne A-B
            request_ab = {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': 2  # Colonne A-B
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
            
            # Formatta colonne D-L
            request_dl = {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 3,
                        'endColumnIndex': 12  # Colonne D-L
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
                body={'requests': [request_ab, request_dl]}
            ).execute()
            
            self.logger.info("✅ Header bold applicato (colonna C preservata)")
            
        except Exception as e:
            self.logger.error(f"❌ Errore formattazione header bold: {e}")
    
    def _format_summary_bold(self, data_rows: int):
        """Formatta riga totali in bold (escludendo colonna C)"""
        try:
            summary_row = data_rows + 3  # Riga dopo i dati + 1 riga vuota
            
            # Formatta colonne A-B
            request_ab = {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': summary_row - 1,
                        'endRowIndex': summary_row,
                        'startColumnIndex': 0,
                        'endColumnIndex': 2  # Colonne A-B
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
            
            # Formatta colonne D-L
            request_dl = {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': summary_row - 1,
                        'endRowIndex': summary_row,
                        'startColumnIndex': 3,
                        'endColumnIndex': 12  # Colonne D-L
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
                body={'requests': [request_ab, request_dl]}
            ).execute()
            
            self.logger.info(f"✅ Summary bold applicato (riga {summary_row}, colonna C preservata)")
            
        except Exception as e:
            self.logger.error(f"❌ Errore formattazione summary bold: {e}")
    
    def _format_conditional_pnl(self, data_rows: int):
        """Applica formattazione condizionale alla colonna PnL % (G) inclusa riga totali"""
        try:
            # Calcola la riga dei totali
            summary_row = data_rows + 3
            
            # Range per la colonna PnL % (dati + totali, escludendo header)
            pnl_range = f"{Config.SHEET_NAME}!G2:G{summary_row}"
            
            # Formattazione percentuale base per tutto il range
            self._format_percentage(pnl_range)
            
            # Formattazione condizionale: rosso per perdite, verde per profitti
            # Scala da -100% a 100% - INCLUDE RIGA TOTALI
            request = {
                'addConditionalFormatRule': {
                    'rule': {
                        'ranges': [{
                            'sheetId': 0,
                            'startRowIndex': 1,  # Riga 2 (dopo header)
                            'endRowIndex': summary_row,  # INCLUDE RIGA TOTALI
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
            
            self.logger.info(f"✅ Formattazione condizionale PnL % applicata (inclusa riga totali {summary_row})")
            
        except Exception as e:
            self.logger.error(f"❌ Errore formattazione condizionale PnL %: {e}")
    
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

    def _update_overview(self, portfolio_data: List[Dict]):
        """Aggiorna tab Overview con storico aggiornamenti"""
        try:
            # Calcola totali in USDT
            total_value_usdt = sum(item['current_value'] for item in portfolio_data)
            
            # Leggi valori dalla riga totale del Portfolio
            summary_values = self._get_portfolio_summary_values()
            total_invested_usdt = summary_values.get('total_invested', 0)
            total_pnl_usdt = summary_values.get('total_pnl', 0)
            pnl_percentage = summary_values.get('pnl_percentage', 0)
            
            # Prepara nuova riga
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_row = [
                current_time,
                f"{total_value_usdt:.2f}",
                f"{total_invested_usdt:.2f}",
                f"{total_pnl_usdt:.2f}",
                f"{pnl_percentage:.4f}"  # Usa 4 decimali per il valore decimale puro
            ]
            
            # Crea tab Overview se non esiste
            self._ensure_sheet_exists(Config.OVERVIEW_SHEET_NAME)
            
            # Scrivi intestazioni se tab vuota
            self._write_overview_headers()
            
            # Aggiungi nuova riga in cima
            self._append_overview_row(new_row)
            
            # Applica formattazione
            self._format_overview()
            
            self.logger.info("✅ Tab Overview aggiornata")
            
        except Exception as e:
            self.logger.error(f"❌ Errore aggiornamento Overview: {e}")
            raise

    def _update_chart(self):
        """Aggiorna tab Grafico con dati per visualizzazione"""
        try:
            # Crea tab Grafico se non esiste
            self._ensure_sheet_exists(Config.CHART_SHEET_NAME)
            
            # Leggi dati da Overview
            overview_data = self._read_overview_data()
            
            if not overview_data:
                self.logger.info("📊 Nessun dato per grafico")
                return
            
            self.logger.info(f"📊 Dati Overview per grafico: {len(overview_data)} righe")
            
            # Prepara dati per grafico
            chart_data = []
            for row in overview_data:
                if len(row) >= 3:  # Almeno data, valore, investito
                    try:
                        date = row[0]
                        
                        # Pulisci valore (rimuovi $ e converti formato europeo)
                        value_str = row[1].replace('$', '').replace(' ', '').strip()
                        if ',' in value_str and '.' in value_str:
                            value_str = value_str.replace('.', '').replace(',', '.')
                        elif ',' in value_str:
                            value_str = value_str.replace(',', '.')
                        value = float(value_str)
                        
                        # Pulisci investito (rimuovi $ e converti formato europeo)
                        invested_str = row[2].replace('$', '').replace(' ', '').strip()
                        if ',' in invested_str and '.' in invested_str:
                            invested_str = invested_str.replace('.', '').replace(',', '.')
                        elif ',' in invested_str:
                            invested_str = invested_str.replace(',', '.')
                        invested = float(invested_str)
                        
                        chart_data.append([date, value, invested])
                        self.logger.info(f"📊 Dato grafico: {date} -> Valore: {value}, Investito: {invested}")
                    except (ValueError, IndexError) as e:
                        self.logger.warning(f"⚠️ Errore conversione riga grafico: {row} - {e}")
                        continue
            
            # Scrivi dati grafico
            self._write_chart_data(chart_data)
            
            # Applica formattazione grafico
            self._format_chart()
            
            # Crea grafico
            self._create_chart()
            
            self.logger.info("✅ Tab Grafico aggiornata")
            
        except Exception as e:
            self.logger.error(f"❌ Errore aggiornamento Grafico: {e}")
            raise

    def _ensure_sheet_exists(self, sheet_name: str):
        """Crea tab se non esiste"""
        try:
            # Controlla se tab esiste
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=Config.GOOGLE_SHEET_ID
            ).execute()
            
            existing_sheets = [sheet['properties']['title'] for sheet in spreadsheet['sheets']]
            
            if sheet_name not in existing_sheets:
                # Crea nuova tab
                request = {
                    'addSheet': {
                        'properties': {
                            'title': sheet_name
                        }
                    }
                }
                
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=Config.GOOGLE_SHEET_ID,
                    body={'requests': [request]}
                ).execute()
                
                self.logger.info(f"✅ Tab '{sheet_name}' creata")
            
        except Exception as e:
            self.logger.error(f"❌ Errore creazione tab {sheet_name}: {e}")
            raise

    def _write_overview_headers(self):
        """Scrive intestazioni tab Overview"""
        try:
            # Scrivi sempre le intestazioni (sovrascrive quelle esistenti)
            range_name = f"{Config.OVERVIEW_SHEET_NAME}!A1:E1"
            body = {'values': [Config.OVERVIEW_HEADERS]}
            self.service.spreadsheets().values().update(
                spreadsheetId=Config.GOOGLE_SHEET_ID,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
                
        except Exception as e:
            self.logger.error(f"❌ Errore scrittura intestazioni Overview: {e}")
            raise

    def _append_overview_row(self, new_row: List[str]):
        """Aggiunge nuova riga in fondo alla tab Overview (ordine cronologico)"""
        try:
            # Leggi tutte le righe esistenti
            result = self.service.spreadsheets().values().get(
                spreadsheetId=Config.GOOGLE_SHEET_ID,
                range=f"{Config.OVERVIEW_SHEET_NAME}!A:E"
            ).execute()
            
            existing_rows = result.get('values', [])
            
            # Trova la prossima riga disponibile (dopo intestazioni)
            next_row = len(existing_rows) + 1
            
            # Scrivi nuova riga in fondo
            range_name = f"{Config.OVERVIEW_SHEET_NAME}!A{next_row}:E{next_row}"
            
            # Prepara valori con tipi corretti per formattazione
            formatted_row = []
            for i, value in enumerate(new_row):
                if i == 0:  # Timestamp (stringa)
                    formatted_row.append(value)
                elif i in [1, 2, 3]:  # Valori USDT (numeri)
                    try:
                        formatted_row.append(float(value))
                    except (ValueError, TypeError):
                        formatted_row.append(value)
                elif i == 4:  # PnL % (numero decimale puro)
                    try:
                        # Assicurati che sia un decimale puro (es: 0.0571 invece di 5.71)
                        pnl_decimal = float(value)
                        formatted_row.append(pnl_decimal)
                    except (ValueError, TypeError):
                        formatted_row.append(value)
                else:
                    formatted_row.append(value)
            
            body = {'values': [formatted_row]}
            self.service.spreadsheets().values().update(
                spreadsheetId=Config.GOOGLE_SHEET_ID,
                range=range_name,
                valueInputOption='USER_ENTERED',  # Permette formattazione automatica
                body=body
            ).execute()
                
        except Exception as e:
            self.logger.error(f"❌ Errore aggiunta riga Overview: {e}")
            raise

    def _insert_row_at_position(self, new_row: List[str], position: int):
        """Inserisce riga in posizione specifica"""
        try:
            # Inserisci riga vuota
            request = {
                'insertDimension': {
                    'range': {
                        'sheetId': self._get_sheet_id(Config.OVERVIEW_SHEET_NAME),
                        'dimension': 'ROWS',
                        'startIndex': position - 1,
                        'endIndex': position
                    }
                }
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=Config.GOOGLE_SHEET_ID,
                body={'requests': [request]}
            ).execute()
            
            # Scrivi nuova riga
            range_name = f"{Config.OVERVIEW_SHEET_NAME}!A{position}:E{position}"
            body = {'values': [new_row]}
            self.service.spreadsheets().values().update(
                spreadsheetId=Config.GOOGLE_SHEET_ID,
                range=range_name,
                valueInputOption='USER_ENTERED',  # Permette formattazione automatica
                body=body
            ).execute()
            
        except Exception as e:
            self.logger.error(f"❌ Errore inserimento riga: {e}")
            raise

    def _get_sheet_id(self, sheet_name: str) -> int:
        """Ottiene ID della tab"""
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=Config.GOOGLE_SHEET_ID
            ).execute()
            
            for sheet in spreadsheet['sheets']:
                if sheet['properties']['title'] == sheet_name:
                    return sheet['properties']['sheetId']
            
            raise ValueError(f"Tab '{sheet_name}' non trovata")
            
        except Exception as e:
            self.logger.error(f"❌ Errore ottenimento ID tab: {e}")
            raise

    def _read_overview_data(self) -> List[List[str]]:
        """Legge dati dalla tab Overview"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=Config.GOOGLE_SHEET_ID,
                range=f"{Config.OVERVIEW_SHEET_NAME}!A:E"
            ).execute()
            
            values = result.get('values', [])
            self.logger.info(f"📊 Dati Overview letti: {len(values)} righe")
            if values:
                self.logger.info(f"📊 Prima riga Overview: {values[0]}")
                if len(values) > 1:
                    self.logger.info(f"📊 Seconda riga Overview: {values[1]}")
            
            return values
            
        except Exception as e:
            self.logger.error(f"❌ Errore lettura dati Overview: {e}")
            return []

    def _write_chart_data(self, chart_data: List[List]):
        """Scrive dati per grafico"""
        try:
            # Pulisci tab grafico
            self.service.spreadsheets().values().clear(
                spreadsheetId=Config.GOOGLE_SHEET_ID,
                range=f"{Config.CHART_SHEET_NAME}!A:C"
            ).execute()
            
            # Scrivi intestazioni
            headers = ['Data', 'Valore Portfolio (USDT)', 'Investito Totale (USDT)']
            range_headers = f"{Config.CHART_SHEET_NAME}!A1:C1"
            body_headers = {'values': [headers]}
            self.service.spreadsheets().values().update(
                spreadsheetId=Config.GOOGLE_SHEET_ID,
                range=range_headers,
                valueInputOption='RAW',
                body=body_headers
            ).execute()
            
            # Scrivi dati
            if chart_data:
                range_data = f"{Config.CHART_SHEET_NAME}!A2:C{len(chart_data)+1}"
                body_data = {'values': chart_data}
                self.service.spreadsheets().values().update(
                    spreadsheetId=Config.GOOGLE_SHEET_ID,
                    range=range_data,
                    valueInputOption='RAW',
                    body=body_data
                ).execute()
                
        except Exception as e:
            self.logger.error(f"❌ Errore scrittura dati grafico: {e}")
            raise

    def _format_overview(self):
        """Applica formattazione tab Overview"""
        try:
            # Formattazione intestazioni bold
            self._format_overview_header_bold()
            
            # Formattazione valuta per colonne B, C, D
            self._format_overview_currency()
            
            # Formattazione percentuale per colonna E
            self._format_overview_percentage()
            
            # Formattazione condizionale PnL %
            self._format_overview_conditional_pnl()
            
        except Exception as e:
            self.logger.error(f"❌ Errore formattazione Overview: {e}")
            raise

    def _format_overview_header_bold(self):
        """Formattazione bold intestazioni Overview"""
        try:
            sheet_id = self._get_sheet_id(Config.OVERVIEW_SHEET_NAME)
            
            request = {
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': 5
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
            
        except Exception as e:
            self.logger.error(f"❌ Errore formattazione bold Overview: {e}")
            raise

    def _format_overview_currency(self):
        """Formattazione dollari Overview"""
        try:
            sheet_id = self._get_sheet_id(Config.OVERVIEW_SHEET_NAME)
            
            # Leggi numero righe per applicare formattazione a tutte le righe
            result = self.service.spreadsheets().values().get(
                spreadsheetId=Config.GOOGLE_SHEET_ID,
                range=f"{Config.OVERVIEW_SHEET_NAME}!A:A"
            ).execute()
            
            data_rows = len(result.get('values', []))
            self.logger.info(f"📊 Applicazione formattazione dollari a {data_rows} righe")
            
            # Formattazione dollari per colonne B, C, D (USDT)
            for col in ['B', 'C', 'D']:
                self.logger.info(f"💵 Formattazione dollari colonna {col}")
                request = {
                    'repeatCell': {
                        'range': {
                            'sheetId': sheet_id,
                            'startRowIndex': 1,  # Escludi intestazioni
                            'endRowIndex': data_rows,
                            'startColumnIndex': ord(col) - ord('A'),
                            'endColumnIndex': ord(col) - ord('A') + 1
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
                
        except Exception as e:
            self.logger.error(f"❌ Errore formattazione valuta Overview: {e}")
            raise

    def _format_overview_percentage(self):
        """Formattazione percentuale Overview"""
        try:
            sheet_id = self._get_sheet_id(Config.OVERVIEW_SHEET_NAME)
            
            # Leggi numero righe per applicare formattazione a tutte le righe
            result = self.service.spreadsheets().values().get(
                spreadsheetId=Config.GOOGLE_SHEET_ID,
                range=f"{Config.OVERVIEW_SHEET_NAME}!A:A"
            ).execute()
            
            data_rows = len(result.get('values', []))
            
            request = {
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': 1,  # Escludi intestazioni
                        'endRowIndex': data_rows,
                        'startColumnIndex': 4,  # Colonna E
                        'endColumnIndex': 5
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
            
        except Exception as e:
            self.logger.error(f"❌ Errore formattazione percentuale Overview: {e}")
            raise

    def _format_overview_conditional_pnl(self):
        """Formattazione condizionale PnL % Overview - Scala verde da 0% a +20%"""
        try:
            sheet_id = self._get_sheet_id(Config.OVERVIEW_SHEET_NAME)
            
            # Leggi numero righe
            result = self.service.spreadsheets().values().get(
                spreadsheetId=Config.GOOGLE_SHEET_ID,
                range=f"{Config.OVERVIEW_SHEET_NAME}!A:A"
            ).execute()
            
            data_rows = len(result.get('values', [])) - 1  # Escludi intestazioni
            
            if data_rows > 0:
                # Aggiungi direttamente la nuova regola di formattazione condizionale
                # Scala verde da 0% a 20%
                request = {
                    'addConditionalFormatRule': {
                        'rule': {
                            'ranges': [{
                                'sheetId': sheet_id,
                                'startRowIndex': 1,
                                'endRowIndex': data_rows + 1,
                                'startColumnIndex': 4,  # Colonna E (PnL %)
                                'endColumnIndex': 5
                            }],
                            'gradientRule': {
                                'minpoint': {
                                    'color': {'red': 0.8, 'green': 0.9, 'blue': 0.8},  # Verde chiaro
                                    'type': 'NUMBER',
                                    'value': '0'  # 0%
                                },
                                'maxpoint': {
                                    'color': {'red': 0.0, 'green': 0.8, 'blue': 0.0},  # Verde scuro
                                    'type': 'NUMBER',
                                    'value': '20'  # +20%
                                }
                            }
                        }
                    }
                }
                
                # Esegui l'operazione
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=Config.GOOGLE_SHEET_ID,
                    body={'requests': [request]}
                ).execute()
                
                self.logger.info(f"✅ Formattazione condizionale Overview PnL% applicata (scala verde 0% a +20%)")
                
        except Exception as e:
            self.logger.error(f"❌ Errore formattazione condizionale Overview: {e}")
            # Non sollevare l'eccezione per non bloccare l'aggiornamento
            pass

    def _format_chart(self):
        """Applica formattazione tab Grafico"""
        try:
            sheet_id = self._get_sheet_id(Config.CHART_SHEET_NAME)
            
            # Formattazione intestazioni bold
            request = {
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': 3
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
            
            # Formattazione dollari per colonne B, C (USDT)
            for col in ['B', 'C']:
                request = {
                    'repeatCell': {
                        'range': {
                            'sheetId': sheet_id,
                            'startColumnIndex': ord(col) - ord('A'),
                            'endColumnIndex': ord(col) - ord('A') + 1
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
                
        except Exception as e:
            self.logger.error(f"❌ Errore formattazione Grafico: {e}")
            raise

    def _get_portfolio_summary_values(self) -> Dict[str, float]:
        """Legge valori dalla riga totale del Portfolio"""
        try:
            # Leggi la riga totale (summary) del Portfolio
            result = self.service.spreadsheets().values().get(
                spreadsheetId=Config.GOOGLE_SHEET_ID,
                range=f"{Config.SHEET_NAME}!E:H"  # Colonne E-H (Valore, Investito, PnL%, PnL USDT)
            ).execute()
            
            values = result.get('values', [])
            self.logger.info(f"📊 Righe trovate nel summary: {len(values)}")
            
            if len(values) > 0:
                # L'ultima riga dovrebbe essere la riga totale
                summary_row = values[-1]
                self.logger.info(f"📊 Riga summary: {summary_row}")
                
                if len(summary_row) >= 4:
                    try:
                        # Pulisci i valori da simboli di valuta e formattazione
                        def clean_value(value_str, is_percentage=False):
                            if not value_str:
                                return 0
                            # Rimuovi simboli di valuta e spazi
                            cleaned = value_str.replace('$', '').replace('€', '').replace(' ', '').strip()
                            
                            # Gestisci formato europeo (es: 4.737,67 -> 4737.67)
                            if ',' in cleaned and '.' in cleaned:
                                # Se ci sono sia virgola che punto, la virgola è il separatore decimale
                                cleaned = cleaned.replace('.', '').replace(',', '.')
                            elif ',' in cleaned:
                                # Se c'è solo virgola, è il separatore decimale
                                cleaned = cleaned.replace(',', '.')
                            
                            # Per le percentuali, rimuovi il simbolo % e dividi per 100
                            if is_percentage:
                                cleaned = cleaned.replace('%', '')
                                value = float(cleaned) if cleaned else 0
                                return value / 100  # Converti da percentuale a decimale
                            else:
                                return float(cleaned) if cleaned else 0
                        
                        total_value = clean_value(summary_row[0])
                        total_invested = clean_value(summary_row[1])
                        pnl_percentage = clean_value(summary_row[2], is_percentage=True)  # Gestisci come percentuale
                        total_pnl = clean_value(summary_row[3])
                        
                        self.logger.info(f"💰 Valori letti - Investito: {total_invested}, PnL: {total_pnl}, PnL%: {pnl_percentage}")
                        
                        return {
                            'total_invested': total_invested,
                            'pnl_percentage': pnl_percentage,
                            'total_pnl': total_pnl
                        }
                    except (ValueError, TypeError) as e:
                        self.logger.error(f"❌ Errore conversione valori: {e}")
                        pass
                else:
                    self.logger.warning(f"⚠️ Riga summary troppo corta: {len(summary_row)} colonne")
            else:
                self.logger.warning("⚠️ Nessuna riga trovata nel summary")
            
            # Fallback se non riesce a leggere
            return {'total_invested': 0, 'pnl_percentage': 0, 'total_pnl': 0}
            
        except Exception as e:
            self.logger.error(f"❌ Errore lettura valori summary: {e}")
            return {'total_invested': 0, 'pnl_percentage': 0, 'total_pnl': 0}

    def _create_chart(self):
        """Crea grafico nella tab Grafico"""
        try:
            sheet_id = self._get_sheet_id(Config.CHART_SHEET_NAME)
            
            # Leggi numero righe dati
            result = self.service.spreadsheets().values().get(
                spreadsheetId=Config.GOOGLE_SHEET_ID,
                range=f"{Config.CHART_SHEET_NAME}!A:A"
            ).execute()
            
            data_rows = len(result.get('values', [])) - 1  # Escludi intestazioni
            
            if data_rows <= 0:
                self.logger.info("📊 Nessun dato per creare grafico")
                return
            
            # Crea grafico
            request = {
                'addChart': {
                    'chart': {
                        'spec': {
                            'title': 'Andamento Portfolio',
                            'basicChart': {
                                'chartType': 'LINE',
                                'legendPosition': 'BOTTOM_LEGEND',
                                'axis': [
                                    {
                                        'position': 'BOTTOM_AXIS',
                                        'title': 'Data'
                                    },
                                    {
                                        'position': 'LEFT_AXIS',
                                        'title': 'Valore (USDT)'
                                    }
                                ],
                                'domains': [
                                    {
                                        'domain': {
                                            'sourceRange': {
                                                'sources': [{
                                                    'sheetId': sheet_id,
                                                    'startRowIndex': 0,
                                                    'endRowIndex': data_rows + 1,
                                                    'startColumnIndex': 0,
                                                    'endColumnIndex': 1
                                                }]
                                            }
                                        }
                                    }
                                ],
                                'series': [
                                    {
                                        'series': {
                                            'sourceRange': {
                                                'sources': [{
                                                    'sheetId': sheet_id,
                                                    'startRowIndex': 0,
                                                    'endRowIndex': data_rows + 1,
                                                    'startColumnIndex': 1,
                                                    'endColumnIndex': 2
                                                }]
                                            }
                                        },
                                        'targetAxis': 'LEFT_AXIS'
                                    },
                                    {
                                        'series': {
                                            'sourceRange': {
                                                'sources': [{
                                                    'sheetId': sheet_id,
                                                    'startRowIndex': 0,
                                                    'endRowIndex': data_rows + 1,
                                                    'startColumnIndex': 2,
                                                    'endColumnIndex': 3
                                                }]
                                            }
                                        },
                                        'targetAxis': 'LEFT_AXIS'
                                    }
                                ]
                            }
                        },
                        'position': {
                            'overlayPosition': {
                                'anchorCell': {
                                    'sheetId': sheet_id,
                                    'rowIndex': 0,
                                    'columnIndex': 5
                                },
                                'widthPixels': 600,
                                'heightPixels': 400
                            }
                        }
                    }
                }
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=Config.GOOGLE_SHEET_ID,
                body={'requests': [request]}
            ).execute()
            
            self.logger.info("✅ Grafico creato")
            
        except Exception as e:
            self.logger.error(f"❌ Errore creazione grafico: {e}")
            raise

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