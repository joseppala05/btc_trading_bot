import pandas as pd
import numpy as np

def calcular_hma(series, period):
    """
    Hull Moving Average - Más reactiva que SMA
    Reduce lag y suaviza mejor que EMA en movimientos rápidos
    """
    half_period = period // 2
    sqrt_period = int(np.sqrt(period))
    
    wma_half = series.rolling(window=half_period).mean()
    wma_full = series.rolling(window=period).mean()
    raw_hma = 2 * wma_half - wma_full
    hma = raw_hma.rolling(window=sqrt_period).mean()
    
    return hma

def analizar_volatilidad_1h(df_1h, ventana_atr=14):
    """
    Calcula:
    1. ATR 14 - grado de volatilidad
    2. HMA 20 - promedio móvil de Hull
    3. ATR_Expansion - Flag: ATR > promedio de últimas 50 velas
    
    Retorna df_1h con nuevas columnas para filtrar operaciones de ALTA volatilidad
    """
    
    # --- 1. CALCULAR ATR ---
    df_1h['TR'] = np.maximum(
        df_1h['Maximo'] - df_1h['Minimo'],
        np.maximum(
            np.abs(df_1h['Maximo'] - df_1h['Cierre'].shift(1)),
            np.abs(df_1h['Minimo'] - df_1h['Cierre'].shift(1))
        )
    )
    
    df_1h['ATR'] = df_1h['TR'].rolling(window=ventana_atr).mean()
    
    # Normalizar ATR como % del cierre para comparación cross-asset
    df_1h['ATR_Pct'] = (df_1h['ATR'] / df_1h['Cierre']) * 100
    
    # --- 2. DETECTAR EXPANSIÓN DE VOLATILIDAD ---
    df_1h['ATR_Media_50'] = df_1h['ATR'].rolling(window=50).mean()
    df_1h['ATR_Expansion'] = df_1h['ATR'] > df_1h['ATR_Media_50'] * 1.1  # >10% encima del promedio
    
    # --- 3. HMA 20 PARA CONFIRMAR DIRECCIÓN ---
    df_1h['HMA_20'] = calcular_hma(df_1h['Cierre'], period=20)
    df_1h['Dir_HMA'] = df_1h['Cierre'] > df_1h['HMA_20']  # True = arriba, False = abajo
    
    return df_1h
