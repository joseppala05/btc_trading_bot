import pandas as pd

def calculate_pivots(df, window=15):
    """
    Identifies local pivots (Supports and Resistances).
    window: Number of candles to the left and right to confirm the pivot.
    """
    window_size = (window * 2) + 1

    # 1. We look for the maximum and minimum in a centered window
    rolling_max = df['Maximo'].rolling(window=window_size, center=True).max()
    rolling_min = df['Minimo'].rolling(window=window_size, center=True).min()

    # 2. We mark the exact price where the pivot occurred (and put NaN where there is none)
    df['Pivote_R'] = df['Maximo'].where(df['Maximo'] == rolling_max)
    df['Pivote_S'] = df['Minimo'].where(df['Minimo'] == rolling_min)

    # 3. THE CRITICAL STEP: Real-time confirmation.
    # We shift the result 'window' candles down (because it takes 5h to confirm it)
    # and drag the value into the future (Forward Fill) to keep the S/R line active.
    df['Resistencia_Activa'] = df['Pivote_R'].shift(window).ffill()
    df['Soporte_Activo'] = df['Pivote_S'].shift(window).ffill()

    # We clean the temporary columns to not dirty the table
    df.drop(columns=['Pivote_R', 'Pivote_S'], inplace=True)

    return df