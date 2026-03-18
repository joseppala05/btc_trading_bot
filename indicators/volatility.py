import pandas as pd
import numpy as np

def calculate_hma(series, period):
    """
    Hull Moving Average - More reactive than SMA
    Reduces lag and smooths better than EMA in fast movements
    """
    half_period = period // 2
    sqrt_period = int(np.sqrt(period))
    
    wma_half = series.rolling(window=half_period).mean()
    wma_full = series.rolling(window=period).mean()
    raw_hma = 2 * wma_half - wma_full
    hma = raw_hma.rolling(window=sqrt_period).mean()
    
    return hma

def analyze_volatility_1h(df_1h, atr_window=14):
    """
    Calculates:
    1. ATR 14 - degree of volatility
    2. HMA 20 - Hull moving average
    3. ATR_Expansion - Flag: ATR > average of last 50 candles
    
    Returns df_1h with new columns to filter HIGH volatility operations
    """
    
    # --- 1. CALCULATE ATR ---
    df_1h['TR'] = np.maximum(
        df_1h['Maximo'] - df_1h['Minimo'],
        np.maximum(
            np.abs(df_1h['Maximo'] - df_1h['Cierre'].shift(1)),
            np.abs(df_1h['Minimo'] - df_1h['Cierre'].shift(1))
        )
    )
    
    df_1h['ATR'] = df_1h['TR'].rolling(window=atr_window).mean()
    
    # Normalize ATR as % of close for cross-asset comparison
    df_1h['ATR_Pct'] = (df_1h['ATR'] / df_1h['Cierre']) * 100
    
    # --- 2. DETECT VOLATILITY EXPANSION ---
    df_1h['ATR_Media_50'] = df_1h['ATR'].rolling(window=50).mean()
    df_1h['ATR_Expansion'] = df_1h['ATR'] > df_1h['ATR_Media_50'] * 1.1  # >10% above the average
    
    # --- 3. HMA 20 TO CONFIRM DIRECTION ---
    df_1h['HMA_20'] = calculate_hma(df_1h['Cierre'], period=20)
    df_1h['Dir_HMA'] = df_1h['Cierre'] > df_1h['HMA_20']  # True = above, False = below
    
    return df_1h
