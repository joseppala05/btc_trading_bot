import pandas as pd

def calculate_trend_and_volume(df):
    """
    Calculates the EMA 50, the volume average and the indecision ratio of the candles.
    """
    # 1. EMA of 50 periods
    df['EMA_50'] = df['Cierre'].ewm(span=50, adjust=False).mean()

    # 2. Simple Moving Average of Volume (20 periods)
    df['Volumen_SMA_20'] = df['Volumen'].rolling(window=20).mean()

    # 3. Indecision: Ratio between the candle body and its total size
    candle_size = df['Maximo'] - df['Minimo']
    candle_size = candle_size.replace(0, 0.00001) # Technical trick to avoid division by zero error
    
    df['Cuerpo_Ratio'] = abs(df['Cierre'] - df['Apertura']) / candle_size

    return df