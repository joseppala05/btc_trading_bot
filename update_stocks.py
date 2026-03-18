import yfinance as yf
import pandas as pd
import os

def download_stock(ticker, timeframe, period):
    print(f"Downloading {ticker} in {timeframe} (Period: {period})...")
    
    # Data download
    df = yf.download(ticker, interval=timeframe, period=period, progress=False)    

    if df.empty:
        print(f"[!] No data found for {ticker} in {timeframe}.")
        return df

    # Correction for new yfinance versions: flatten columns if they come with extra levels
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Clean and format to be identical to Binance (CCXT)
    df = df.reset_index()
    
    # yfinance returns 'Date' for 1d and 'Datetime' for intraday (1h, 15m)
    date_column = 'Datetime' if 'Datetime' in df.columns else 'Date'
    
    # Rename columns to unify with the backtest engine
    df = df.rename(columns={
        date_column: 'Fecha',
        'Open': 'Apertura',
        'High': 'Maximo',
        'Low': 'Minimo',
        'Close': 'Cierre',
        'Volume': 'Volumen'
    })
    
    # Select only the necessary columns
    columns = ['Fecha', 'Apertura', 'Maximo', 'Minimo', 'Cierre', 'Volumen']
    df = df[columnas].copy()

    # Data cleaning: Ensure prices are floats (real numbers)
    for col in ['Apertura', 'Maximo', 'Minimo', 'Cierre']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Remove time zones to avoid comparison errors with Binance data
    df['Fecha'] = pd.to_datetime(df['Fecha']).dt.tz_localize(None)
    
    # Remove possible empty rows after conversion
    return df.dropna()

if __name__ == "__main__":
    os.makedirs('data', exist_ok=True)
    
    # List of the 5 famous stocks
    stocks = ['AAPL', 'TSLA', 'MSFT', 'AMZN', 'NVDA']
    
    # Timeframe configuration (Yahoo Finance limits)
    download_config = [
        ('1d', '2y'),   # 1 Day: 2 years
        ('1h', '730d'), # 1 Hour: ~2 years
        ('15m', '60d')  # 15 Min: Maximum 60 days
    ]
    
    for ticker in stocks:
        filename = ticker.lower()
        print(f"\n======================================")
        print(f"=== DOWNLOADING DATA FOR {ticker} ===")
        print(f"======================================")
        
        for timeframe, period in download_config:
            df_stock = download_stock(ticker, timeframe, period)
            
            if not df_stock.empty:
                save_path = f'data/{filename}_{timeframe}.csv'
                df_stock.to_csv(save_path, index=False)
                print(f"[OK] Saved: {save_path} ({len(df_stock)} rows)")
                
    print("\nStocks Database Synchronized and ready!")