"""
Client per Binance API
Gestisce la connessione e il recupero dei dati del portafoglio (Spot + Simple Earn)
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
        # Usa direttamente le variabili d'ambiente per evitare problemi di caricamento
        import os
        api_key = os.getenv('BINANCE_API_KEY')
        secret_key = os.getenv('BINANCE_SECRET_KEY')
        
        if not api_key or not secret_key:
            raise ValueError("BINANCE_API_KEY e BINANCE_SECRET_KEY devono essere impostati")
        
        self.client = Client(api_key, secret_key)
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
            
            self.logger.info(f"✅ Trovati {len(non_zero_balances)} asset con saldo > 0 nel wallet Spot")
            return non_zero_balances
            
        except Exception as e:
            self.logger.error(f"❌ Errore nel recupero saldi spot: {e}")
            raise
    
    def get_simple_earn_account(self) -> Dict:
        """Ottiene le informazioni del Simple Earn account"""
        try:
            account_info = self.client.get_simple_earn_account()
            self.logger.info("✅ Informazioni Simple Earn account recuperate con successo")
            return account_info
        except BinanceAPIException as e:
            self.logger.error(f"❌ Errore nel recupero Simple Earn account: {e}")
            return {}
    
    def get_simple_earn_positions(self) -> List[Dict]:
        """Ottiene le posizioni Simple Earn (Flexible + Locked)"""
        try:
            positions = []
            
            # Recupera posizioni Flexible
            try:
                flexible_data = self.client.get_simple_earn_flexible_product_position()
                if flexible_data and 'rows' in flexible_data:
                    for pos in flexible_data['rows']:
                        pos['type'] = 'Flexible'
                        pos['source'] = 'Simple Earn'
                        positions.append(pos)
                    self.logger.info(f"✅ Trovate {len(flexible_data['rows'])} posizioni Simple Earn Flexible")
            except Exception as e:
                self.logger.warning(f"⚠️ Errore nel recupero posizioni Flexible: {e}")
            
            # Recupera posizioni Locked
            try:
                locked_data = self.client.get_simple_earn_locked_product_position()
                if locked_data and 'rows' in locked_data:
                    for pos in locked_data['rows']:
                        pos['type'] = 'Locked'
                        pos['source'] = 'Simple Earn'
                        positions.append(pos)
                    self.logger.info(f"✅ Trovate {len(locked_data['rows'])} posizioni Simple Earn Locked")
            except Exception as e:
                self.logger.warning(f"⚠️ Errore nel recupero posizioni Locked: {e}")
            
            return positions
            
        except Exception as e:
            self.logger.error(f"❌ Errore nel recupero posizioni Simple Earn: {e}")
            return []
    
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
        """Ottiene i dati completi del portafoglio (Spot + Simple Earn)"""
        try:
            portfolio_data = []
            
            # 1. Recupera dati Spot
            spot_balances = self.get_spot_balances()
            spot_symbols = [balance['asset'] for balance in spot_balances]
            
            # 2. Recupera dati Simple Earn
            earn_positions = self.get_simple_earn_positions()
            earn_symbols = [pos['asset'] for pos in earn_positions]
            
            # 3. Combina tutti i simboli per i prezzi
            all_symbols = list(set(spot_symbols + earn_symbols))
            prices = self.get_current_prices(all_symbols)
            
            # 4. Elabora dati Spot
            for balance in spot_balances:
                asset = balance['asset']
                free_qty = float(balance['free'])
                locked_qty = float(balance['locked'])
                total_qty = free_qty + locked_qty
                
                if total_qty > 0:
                    current_price = prices.get(asset, 0.0)
                    current_value = total_qty * current_price
                    
                    # Per ora assumiamo prezzo medio = prezzo corrente
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
                        'pnl_euro': pnl_euro,
                        'source': 'Spot',
                        'type': 'Spot'
                    })
            
            # 5. Elabora dati Simple Earn
            for position in earn_positions:
                asset = position['asset']
                total_amount = float(position['totalAmount'])
                
                if total_amount > 0:
                    current_price = prices.get(asset, 0.0)
                    current_value = total_amount * current_price
                    
                    # Per Simple Earn, assumiamo prezzo medio = prezzo corrente
                    avg_price = current_price
                    total_invested = total_amount * avg_price
                    
                    # Calcolo PnL (inclusi i rewards)
                    cumulative_rewards = float(position.get('cumulativeTotalRewards', 0))
                    pnl_euro = current_value - total_invested + (cumulative_rewards * current_price)
                    pnl_percentage = (pnl_euro / total_invested * 100) if total_invested > 0 else 0
                    
                    # APR per Simple Earn
                    apr = float(position.get('latestAnnualPercentageRate', 0)) * 100
                    
                    portfolio_data.append({
                        'asset': asset,
                        'quantity': total_amount,
                        'avg_price': avg_price,
                        'current_price': current_price,
                        'current_value': current_value,
                        'total_invested': total_invested,
                        'pnl_percentage': pnl_percentage,
                        'pnl_euro': pnl_euro,
                        'source': 'Simple Earn',
                        'type': position.get('type', 'Flexible'),
                        'apr': apr,
                        'cumulative_rewards': cumulative_rewards
                    })
            
            # 6. Combina asset duplicati (se presenti sia in Spot che Earn)
            combined_data = {}
            for item in portfolio_data:
                asset = item['asset']
                if asset in combined_data:
                    # Combina i dati
                    existing = combined_data[asset]
                    combined_data[asset] = {
                        'asset': asset,
                        'quantity': existing['quantity'] + item['quantity'],
                        'avg_price': (existing['avg_price'] + item['avg_price']) / 2,  # Media semplice
                        'current_price': item['current_price'],
                        'current_value': existing['current_value'] + item['current_value'],
                        'total_invested': existing['total_invested'] + item['total_invested'],
                        'pnl_percentage': 0,  # Ricalcolato dopo
                        'pnl_euro': existing['pnl_euro'] + item['pnl_euro'],
                        'source': f"{existing['source']} + {item['source']}",
                        'type': 'Combined'
                    }
                else:
                    combined_data[asset] = item
            
            # Ricalcola PnL per asset combinati
            for asset, item in combined_data.items():
                if item['total_invested'] > 0:
                    item['pnl_percentage'] = (item['pnl_euro'] / item['total_invested']) * 100
            
            # Converti in lista e ordina per valore
            final_data = list(combined_data.values())
            final_data.sort(key=lambda x: x['current_value'], reverse=True)
            
            self.logger.info(f"✅ Dati portafoglio elaborati per {len(final_data)} asset (Spot + Simple Earn)")
            return final_data
            
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