#!/usr/bin/env python3
"""
Test del sistema Crypto Portfolio Tracker (Spot + Simple Earn)
"""
import os
import json
from dotenv import load_dotenv
from binance.client import Client
from datetime import datetime

def main():
    """Test del sistema"""
    load_dotenv()
    
    print('🔍 Test Sistema Completo (Spot + Simple Earn)')
    print('=' * 50)
    
    try:
        # Inizializza client
        client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_SECRET_KEY'))
        
        # 1. Test Simple Earn
        print('\n📊 Simple Earn:')
        earn_account = client.get_simple_earn_account()
        total_earn_usdt = float(earn_account['totalAmountInUSDT'])
        print(f'💰 Totale Simple Earn: {total_earn_usdt:,.2f} USDT')
        
        flexible_data = client.get_simple_earn_flexible_product_position()
        flexible_positions = flexible_data.get('rows', [])
        print(f'📊 Posizioni Flexible: {len(flexible_positions)}')
        
        locked_data = client.get_simple_earn_locked_product_position()
        locked_positions = locked_data.get('rows', [])
        print(f'📊 Posizioni Locked: {len(locked_positions)}')
        
        # 2. Test Spot Wallet
        print('\n📊 Spot Wallet:')
        account_info = client.get_account()
        balances = account_info['balances']
        non_zero_balances = [b for b in balances if float(b['free']) > 0 or float(b['locked']) > 0]
        print(f'📊 Asset con saldo > 0: {len(non_zero_balances)}')
        
        # 3. Elabora dati Simple Earn
        print('\n📊 Elaborazione Simple Earn:')
        earn_assets = []
        for pos in flexible_positions + locked_positions:
            asset = pos['asset']
            amount = float(pos['totalAmount'])
            if amount > 0:
                # Prova a ottenere il prezzo
                try:
                    ticker = client.get_symbol_ticker(symbol=f'{asset}USDT')
                    price = float(ticker['price'])
                    value = amount * price
                    apr = float(pos.get('latestAnnualPercentageRate', 0)) * 100
                    
                    earn_assets.append({
                        'asset': asset,
                        'amount': amount,
                        'price': price,
                        'value': value,
                        'apr': apr,
                        'type': 'Flexible' if pos in flexible_positions else 'Locked'
                    })
                except:
                    print(f'  ⚠️ Prezzo non disponibile per {asset}')
        
        # 4. Elabora dati Spot
        print('\n📊 Elaborazione Spot:')
        spot_assets = []
        for balance in non_zero_balances:
            asset = balance['asset']
            free = float(balance['free'])
            locked = float(balance['locked'])
            total = free + locked
            
            if total > 0:
                try:
                    ticker = client.get_symbol_ticker(symbol=f'{asset}USDT')
                    price = float(ticker['price'])
                    value = total * price
                    
                    spot_assets.append({
                        'asset': asset,
                        'amount': total,
                        'price': price,
                        'value': value,
                        'free': free,
                        'locked': locked
                    })
                except:
                    print(f'  ⚠️ Prezzo non disponibile per {asset}')
        
        # 5. Combina e ordina
        all_assets = []
        
        # Aggiungi Simple Earn
        for asset in earn_assets:
            all_assets.append({
                'asset': asset['asset'],
                'amount': asset['amount'],
                'price': asset['price'],
                'value': asset['value'],
                'source': 'Simple Earn',
                'type': asset['type'],
                'apr': asset['apr']
            })
        
        # Aggiungi Spot
        for asset in spot_assets:
            all_assets.append({
                'asset': asset['asset'],
                'amount': asset['amount'],
                'price': asset['price'],
                'value': asset['value'],
                'source': 'Spot',
                'type': 'Spot'
            })
        
        # Ordina per valore
        all_assets.sort(key=lambda x: x['value'], reverse=True)
        
        # 6. Risultati
        print('\n🎯 Risultati:')
        print(f'📊 Asset totali: {len(all_assets)}')
        print(f'📊 Asset Simple Earn: {len(earn_assets)}')
        print(f'📊 Asset Spot: {len(spot_assets)}')
        
        total_value = sum(asset['value'] for asset in all_assets)
        print(f'💰 Valore totale: ${total_value:,.2f}')
        
        print('\n🏆 Top 10 Asset:')
        for i, asset in enumerate(all_assets[:10]):
            source = asset['source']
            asset_type = asset.get('type', 'N/A')
            apr = asset.get('apr', 0)
            
            print(f'{i+1:2d}. {asset["asset"]:6s}: ${asset["value"]:8.2f} ({source} - {asset_type})', end='')
            if apr > 0:
                print(f' [APR: {apr:.2f}%]')
            else:
                print()
        
        print('\n🎉 Test completato con successo!')
        
        # 7. Salva risultati per debug
        with open('test_results.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_assets': len(all_assets),
                'total_value': total_value,
                'earn_assets': len(earn_assets),
                'spot_assets': len(spot_assets),
                'assets': all_assets
            }, f, indent=2)
        
        print('💾 Risultati salvati in test_results.json')
        
    except Exception as e:
        print(f'❌ Errore: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 