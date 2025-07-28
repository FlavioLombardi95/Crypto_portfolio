"""
Configurazione per Crypto Portfolio Tracker
"""
import os
from typing import Dict, Any

class Config:
    """Classe di configurazione per il progetto"""
    
    # Binance API Configuration
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
    BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
    BINANCE_BASE_URL = 'https://api.binance.com'
    
    # Google Sheets Configuration
    GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
    GOOGLE_SHEETS_CREDENTIALS = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
    
    # Sheet Configuration
    SHEET_NAME = 'Portfolio'
    START_ROW = 2  # Prima riga dopo le intestazioni
    
    # Column mappings per Google Sheets
    COLUMNS = {
        'asset': 'A',
        'quantity': 'B', 
        'avg_price': 'C',
        'current_price': 'D',
        'current_value': 'E',
        'total_invested': 'F',
        'pnl_percentage': 'G',
        'pnl_euro': 'H',
        'last_update': 'I'
    }
    
    # Headers per il Google Sheet
    HEADERS = [
        'Asset',
        'Quantità', 
        'Prezzo Medio',
        'Prezzo Attuale',
        'Valore Attuale',
        'Investito Totale',
        'PnL %',
        'PnL €',
        'Ultimo Aggiornamento'
    ]
    
    # Configurazione per il calcolo PnL
    BASE_CURRENCY = 'EUR'
    
    # Configurazione per il logging
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configurazione per l'aggiornamento
    UPDATE_INTERVAL_HOURS = 1
    
    @classmethod
    def validate_config(cls) -> bool:
        """Valida che tutte le configurazioni necessarie siano presenti"""
        required_vars = [
            'BINANCE_API_KEY',
            'BINANCE_SECRET_KEY', 
            'GOOGLE_SHEET_ID',
            'GOOGLE_SHEETS_CREDENTIALS'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Configurazioni mancanti: {', '.join(missing_vars)}")
            print("Assicurati di aver impostato tutti i GitHub Secrets necessari")
            return False
        
        return True
    
    @classmethod
    def get_sheet_range(cls, start_row: int = None, end_row: int = None) -> str:
        """Genera il range per Google Sheets"""
        if start_row is None:
            start_row = cls.START_ROW
        
        if end_row is None:
            end_row = start_row + 1000  # Range ampio per sicurezza
        
        return f"{cls.SHEET_NAME}!A{start_row}:I{end_row}"
    
    @classmethod
    def get_column_letter(cls, column_name: str) -> str:
        """Ottiene la lettera della colonna per il nome specificato"""
        return cls.COLUMNS.get(column_name, 'A') 