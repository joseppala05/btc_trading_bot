import pandas as pd

def analyze_macro_1d(df_1d, window=5):
    """
    Analiza el gráfico diario para encontrar S/R institucionales y
    confirmar rupturas reales usando la regla de las 2 velas.
    """
    window_size = (window * 2) + 1

    # --- 1. IDENTIFY WALLS (Macro Supports and Resistances) ---
    rolling_max = df_1d['Maximo'].rolling(window=window_size, center=True).max()
    rolling_min = df_1d['Minimo'].rolling(window=window_size, center=True).min()

    df_1d['Pivot_R'] = df_1d['Maximo'].where(df_1d['Maximo'] == rolling_max)
    df_1d['Pivot_S'] = df_1d['Minimo'].where(df_1d['Minimo'] == rolling_min)

    # Drag the confirmed level into the future
    df_1d['Macro_Resistance'] = df_1d['Pivot_R'].shift(window).ffill()
    df_1d['Macro_Support'] = df_1d['Pivot_S'].shift(window).ffill()

    df_1d.drop(columns=['Pivote_R', 'Pivote_S'], inplace=True)

    # --- 2. REGLA DE RUPTURA CONFIRMADA (2 VELAS) ---
    
    # Resistance Breakout (Bullish)
    # Candle T-1 closes above R
    broke_r_yesterday = df_1d['Cierre'].shift(1) > df_1d['Macro_Resistance'].shift(1)
    # Candle T closes above R
    confirms_r_today = df_1d['Cierre'] > df_1d['Macro_Resistance']
    
    df_1d['R_Broken'] = broke_r_yesterday & confirms_r_today

    # Support Breakout (Bearish)
    # Candle T-1 closes below S
    broke_s_yesterday = df_1d['Cierre'].shift(1) < df_1d['Macro_Support'].shift(1)
    # Candle T closes below S
    confirms_s_today = df_1d['Cierre'] < df_1d['Macro_Support']
    
    df_1d['S_Broken'] = broke_s_yesterday & confirms_s_today

    df_1d['EMA_200_Macro'] = df_1d['Cierre'].ewm(span=200, adjust=False).mean()


    return df_1d