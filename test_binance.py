#!/usr/bin/env python3
"""
Script di test per Binance API
"""
import os
from dotenv import load_dotenv
from binance.client import Client
from binance.exceptions import BinanceAPIException

def test_binance_connection():
    """Testa la connessione a Binance API"""
    
    # Carica le variabili d'ambiente
    load_dotenv()
    
    # Ottieni le credenziali
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    print("🔍 Test Connessione Binance API")
    print("=" * 40)
    
    # Verifica che le credenziali siano presenti
    if not api_key or not secret_key:
        print("❌ Credenziali mancanti nel file .env")
        print("Assicurati di aver configurato:")
        print("- BINANCE_API_KEY")
        print("- BINANCE_SECRET_KEY")
        return False
    
    print(f"✅ API Key trovata: {api_key[:8]}...{api_key[-4:]}")
    print(f"✅ Secret Key trovato: {secret_key[:8]}...{secret_key[-4:]}")
    
    try:
        # Crea il client
        client = Client(api_key, secret_key)
        
        # Test connessione - ottieni server time
        server_time = client.get_server_time()
        print(f"✅ Connessione riuscita! Server time: {server_time}")
        
        # Test account info
        account_info = client.get_account()
        print(f"✅ Account info recuperata")
        
        # Mostra saldi non zero
        balances = account_info['balances']
        non_zero_balances = [
            balance for balance in balances 
            if float(balance['free']) > 0 or float(balance['locked']) > 0
        ]
        
        print(f"📊 Trovati {len(non_zero_balances)} asset con saldo > 0:")
        
        if non_zero_balances:
            for balance in non_zero_balances:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                print(f"  - {asset}: {total} (free: {free}, locked: {locked})")
        else:
            print("  ⚠️ Nessun asset trovato nel portafoglio")
        
        return True
        
    except BinanceAPIException as e:
        print(f"❌ Errore API Binance: {e}")
        return False
    except Exception as e:
        print(f"❌ Errore generico: {e}")
        return False

if __name__ == "__main__":
    success = test_binance_connection()
    
    if success:
        print("\n🎉 Test completato con successo!")
        print("Puoi procedere con il setup completo del sistema.")
    else:
        print("\n❌ Test fallito. Controlla le credenziali e riprova.") 