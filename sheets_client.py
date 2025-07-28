"""
Client per Google Sheets API
Gestisce la scrittura e lettura dei dati nel foglio di calcolo (Spot + Simple Earn)
"""
import logging
import json
from typing import List, Dict, Any
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from config import Config

class GoogleSheetsClient:
    """Client per interagire con Google Sheets API"""
    
    def __init__(self):
        """Inizializza il client Google Sheets"""
        self.logger = logging.getLogger(__name__)
        self.service = self._create_service()
        
    def _create_service(self):
        """Crea il servizio Google Sheets"""
        try:
            # Parsing delle credenziali dal JSON string
            credentials_info = json.loads(Config.GOOGLE_SHEETS_CREDENTIALS)
            
            # Creazione delle credenziali
            credentials = Credentials.from_service_account_info(
                credentials_info,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            # Creazione del servizio
            service = build('sheets', 'v4', credentials=credentials)
            self.logger.info("✅ Servizio Google Sheets creato con successo")
            return service
            
        except Exception as e:
            self.logger.error(f"❌ Errore nella creazione del servizio Google Sheets: {e}")
            raise
    
    def clear_sheet(self, range_name: str = None):
        """Pulisce il foglio di calcolo"""
        try:
            if range_name is None:
                range_name = Config.get_sheet_range()
            
            self.service.spreadsheets().values().clear(
                spreadsheetId=Config.GOOGLE_SHEET_ID,
                range=range_name
            ).execute()
            
            self.logger.info(f"✅ Foglio pulito: {range_name}")
            
        except HttpError as e:
            self.logger.error(f"❌ Errore nella pulizia del foglio: {e}")
            raise
    
    def write_headers(self):
        """Scrive le intestazioni nel foglio"""
        try:
            range_name = f"{Config.SHEET_NAME}!A1:L1"
            
            # Intestazioni estese per Spot + Simple Earn
            headers = [
                'Asset',
                'Quantità', 
                'Prezzo Medio',
                'Prezzo Attuale',
                'Valore Attuale',
                'Investito Totale',
                'PnL %',
                'PnL €',
                'Fonte',
                'Tipo',
                'APR %',
                'Ultimo Aggiornamento'
            ]
            
            body = {
                'values': [headers]
            }
            
            self.service.spreadsheets().values().update(
                spreadsheetId=Config.GOOGLE_SHEET_ID,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            self.logger.info("✅ Intestazioni scritte con successo")
            
        except HttpError as e:
            self.logger.error(f"❌ Errore nella scrittura delle intestazioni: {e}")
            raise
    
    def write_portfolio_data(self, portfolio_data: List[Dict]):
        """Scrive i dati del portafoglio nel foglio"""
        try:
            if not portfolio_data:
                self.logger.warning("⚠️ Nessun dato da scrivere")
                return
            
            # Prepara i dati per la scrittura
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
                    item.get('source', 'N/A'),
                    item.get('type', 'N/A'),
                    round(item.get('apr', 0), 2),
                    current_time
                ]
                values.append(row)
            
            # Scrivi i dati
            range_name = f"{Config.SHEET_NAME}!A2:L{len(values)+1}"
            body = {
                'values': values
            }
            
            self.service.spreadsheets().values().update(
                spreadsheetId=Config.GOOGLE_SHEET_ID,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            self.logger.info(f"✅ {len(values)} righe scritte nel foglio")
            
        except HttpError as e:
            self.logger.error(f"❌ Errore nella scrittura dei dati: {e}")
            raise
    
    def read_portfolio_data(self) -> List[List]:
        """Legge i dati dal foglio"""
        try:
            range_name = f"{Config.SHEET_NAME}!A2:L1000"
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=Config.GOOGLE_SHEET_ID,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            self.logger.info(f"✅ {len(values)} righe lette dal foglio")
            return values
            
        except HttpError as e:
            self.logger.error(f"❌ Errore nella lettura dei dati: {e}")
            return []
    
    def update_cell(self, row: int, column: str, value: Any):
        """Aggiorna una singola cella"""
        try:
            range_name = f"{Config.SHEET_NAME}!{column}{row}"
            
            body = {
                'values': [[value]]
            }
            
            self.service.spreadsheets().values().update(
                spreadsheetId=Config.GOOGLE_SHEET_ID,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            self.logger.info(f"✅ Cella {range_name} aggiornata con valore: {value}")
            
        except HttpError as e:
            self.logger.error(f"❌ Errore nell'aggiornamento della cella: {e}")
            raise
    
    def add_summary_row(self, portfolio_data: List[Dict]):
        """Aggiunge una riga di riepilogo con i totali"""
        try:
            if not portfolio_data:
                return
            
            # Calcola i totali
            total_current_value = sum(item['current_value'] for item in portfolio_data)
            total_invested = sum(item['total_invested'] for item in portfolio_data)
            total_pnl_euro = sum(item['pnl_euro'] for item in portfolio_data)
            total_pnl_percentage = (total_pnl_euro / total_invested * 100) if total_invested > 0 else 0
            
            # Trova l'ultima riga con dati
            existing_data = self.read_portfolio_data()
            next_row = len(existing_data) + 2  # +2 perché partiamo dalla riga 2
            
            # Aggiungi una riga vuota
            self.update_cell(next_row, 'A', '')
            next_row += 1
            
            # Aggiungi la riga di riepilogo
            summary_row = [
                'TOTALE',
                '',
                '',
                '',
                round(total_current_value, 2),
                round(total_invested, 2),
                round(total_pnl_percentage, 2),
                round(total_pnl_euro, 2),
                'Spot + Simple Earn',
                'Combined',
                '',
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ]
            
            range_name = f"{Config.SHEET_NAME}!A{next_row}:L{next_row}"
            body = {
                'values': [summary_row]
            }
            
            self.service.spreadsheets().values().update(
                spreadsheetId=Config.GOOGLE_SHEET_ID,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            self.logger.info("✅ Riga di riepilogo aggiunta")
            
        except HttpError as e:
            self.logger.error(f"❌ Errore nell'aggiunta della riga di riepilogo: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Testa la connessione a Google Sheets"""
        try:
            # Prova a leggere le intestazioni
            range_name = f"{Config.SHEET_NAME}!A1:L1"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=Config.GOOGLE_SHEET_ID,
                range=range_name
            ).execute()
            
            self.logger.info("✅ Connessione a Google Sheets riuscita")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Errore di connessione a Google Sheets: {e}")
            return False 