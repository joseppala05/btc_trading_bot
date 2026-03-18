import ccxt
import pandas as pd
import os
import time

def download_historical(symbol='BTC/USDT', timeframe='1d', limit_candles=1000):
    exchange = ccxt.binance()
    print(f"Downloading {limit_candles} candles of {timeframe} for {symbol}...")
    
    now = exchange.milliseconds()
    multiplier = {'1d': 24*60*60, '1h': 60*60, '15m': 15*60}
    start_timestamp = now - (limit_candles * multiplier[timeframe] * 1000) 
    
    raw_data = []
    
    while len(raw_data) < limit_candles:
        try:
            # Request blocks of 1000
            block = exchange.fetch_ohlcv(symbol, timeframe, since=start_timestamp, limit=1000)
            if not block: break
            start_timestamp = block[-1][0] + 1
            raw_data.extend(block)
            time.sleep(0.3) # Safety pause for 1 year of data
        except Exception as e:
            print(f"Error in download: {e}")
            break

    # Trim in case Binance returns an extra pair
    raw_data = raw_data[-limit_candles:]
    df = pd.DataFrame(raw_data, columns=['Fecha', 'Apertura', 'Maximo', 'Minimo', 'Cierre', 'Volumen'])
    df['Fecha'] = pd.to_datetime(df['Fecha'], unit='ms')
    return df

if __name__ == "__main__":
    os.makedirs('data', exist_ok=True)
    history_days = 365*2 # 2 YEARS FULL (Note: your comment says 1 year but variable multiplies by 2)
    
    # Only cryptocurrencies here, since Binance doesn't have stocks
    coins = [ 'XRP/USDT', 'ADA/USDT'] # 'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'ADA/USDT'
    
    for symbol in coins:
        name = symbol.split('/')[0].lower() # Extract 'btc', 'eth', 'sol', 'xrp', 'ada'
        print(f"\n======================================")
        print(f"=== DOWNLOADING DATA FOR {name.upper()} ===")
        print(f"======================================")
        
        # 1. Macro (1D)
        df_1d = download_historical(symbol=symbol, timeframe='1d', limit_candles=history_days)
        df_1d.to_csv(f'data/{name}_1d.csv', index=False)
        
        # 2. Setup (1H)
        df_1h = download_historical(symbol=symbol, timeframe='1h', limit_candles=history_days * 24)
        df_1h.to_csv(f'data/{name}_1h.csv', index=False)
        
        # 3. Trigger (15m)
        df_15m = download_historical(symbol=symbol, timeframe='15m', limit_candles=history_days * 24 * 4)
        df_15m.to_csv(f'data/{name}_15m.csv', index=False)
    
    downloaded_cryptos = ", ".join([m.split('/')[0] for m in coins])
    print(f"\nDatabase Synchronized ({downloaded_cryptos}) ready to operate!")