"""
Client per Binance API
Gestisce la connessione e il recupero dei dati del portafoglio
"""
import logging
from typing import Dict, List, Optional
from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd
from config import Config

class BinanceClient:
    """Client per interagire con l'API di Binance"""
    
    def __init__(self):
        """Inizializza il client Binance"""
        self.client = Client(Config.BINANCE_API_KEY, Config.BINANCE_SECRET_KEY)
        self.logger = logging.getLogger(__name__)
        
    def get_account_info(self) -> Dict:
        """Ottiene le informazioni dell'account"""
        try:
            account_info = self.client.get_account()
            self.logger.info("✅ Informazioni account recuperate con successo")
            return account_info
        except BinanceAPIException as e:
            self.logger.error(f"❌ Errore nel recupero informazioni account: {e}")
            raise
    
    def get_spot_balances(self) -> List[Dict]:
        """Ottiene i saldi del portafoglio spot"""
        try:
            account_info = self.get_account_info()
            balances = account_info['balances']
            
            # Filtra solo i saldi con quantità > 0
            non_zero_balances = [
                balance for balance in balances 
                if float(balance['free']) > 0 or float(balance['locked']) > 0
            ]
            
            self.logger.info(f"✅ Trovati {len(non_zero_balances)} asset con saldo > 0")
            return non_zero_balances
            
        except Exception as e:
            self.logger.error(f"❌ Errore nel recupero saldi spot: {e}")
            raise
    
    def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Ottiene i prezzi correnti per una lista di simboli"""
        try:
            prices = {}
            
            for symbol in symbols:
                if symbol == 'EUR':
                    prices[symbol] = 1.0  # EUR è la valuta base
                    continue
                    
                try:
                    # Prova prima con EUR come quote currency
                    ticker = self.client.get_symbol_ticker(symbol=f"{symbol}EUR")
                    prices[symbol] = float(ticker['price'])
                except BinanceAPIException:
                    try:
                        # Se non esiste, prova con USDT
                        ticker = self.client.get_symbol_ticker(symbol=f"{symbol}USDT")
                        usdt_price = float(ticker['price'])
                        
                        # Converti USDT in EUR (approssimativo)
                        eur_ticker = self.client.get_symbol_ticker(symbol="EURUSDT")
                        eur_rate = float(eur_ticker['price'])
                        prices[symbol] = usdt_price / eur_rate
                    except BinanceAPIException:
                        self.logger.warning(f"⚠️ Prezzo non trovato per {symbol}")
                        prices[symbol] = 0.0
            
            self.logger.info(f"✅ Prezzi recuperati per {len(prices)} asset")
            return prices
            
        except Exception as e:
            self.logger.error(f"❌ Errore nel recupero prezzi: {e}")
            raise
    
    def get_portfolio_data(self) -> List[Dict]:
        """Ottiene i dati completi del portafoglio"""
        try:
            balances = self.get_spot_balances()
            symbols = [balance['asset'] for balance in balances]
            prices = self.get_current_prices(symbols)
            
            portfolio_data = []
            
            for balance in balances:
                asset = balance['asset']
                free_qty = float(balance['free'])
                locked_qty = float(balance['locked'])
                total_qty = free_qty + locked_qty
                
                if total_qty > 0:
                    current_price = prices.get(asset, 0.0)
                    current_value = total_qty * current_price
                    
                    # Per ora assumiamo prezzo medio = prezzo corrente
                    # In futuro si può implementare il calcolo del prezzo medio dalle transazioni
                    avg_price = current_price
                    total_invested = total_qty * avg_price
                    
                    # Calcolo PnL
                    pnl_euro = current_value - total_invested
                    pnl_percentage = (pnl_euro / total_invested * 100) if total_invested > 0 else 0
                    
                    portfolio_data.append({
                        'asset': asset,
                        'quantity': total_qty,
                        'avg_price': avg_price,
                        'current_price': current_price,
                        'current_value': current_value,
                        'total_invested': total_invested,
                        'pnl_percentage': pnl_percentage,
                        'pnl_euro': pnl_euro
                    })
            
            # Ordina per valore attuale decrescente
            portfolio_data.sort(key=lambda x: x['current_value'], reverse=True)
            
            self.logger.info(f"✅ Dati portafoglio elaborati per {len(portfolio_data)} asset")
            return portfolio_data
            
        except Exception as e:
            self.logger.error(f"❌ Errore nell'elaborazione dati portafoglio: {e}")
            raise
    
    def get_historical_prices(self, symbol: str, interval: str = '1d', limit: int = 30) -> List[Dict]:
        """Ottiene i prezzi storici per un simbolo"""
        try:
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            historical_data = []
            for kline in klines:
                historical_data.append({
                    'timestamp': kline[0],
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5])
                })
            
            return historical_data
            
        except BinanceAPIException as e:
            self.logger.error(f"❌ Errore nel recupero prezzi storici per {symbol}: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Testa la connessione all'API di Binance"""
        try:
            server_time = self.client.get_server_time()
            self.logger.info("✅ Connessione a Binance API riuscita")
            return True
        except Exception as e:
            self.logger.error(f"❌ Errore di connessione a Binance API: {e}")
            return False 