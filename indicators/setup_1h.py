import pandas as pd
import numpy as np

def analyze_setup_1h(df_1h, df_1d, zone_margin=0.05):
    # 1. SYNCHRONIZE CLOCKS
    df_1h['Date_Day'] = df_1h['Fecha'].dt.floor('d')
    daily_walls = df_1d[['Fecha', 'Macro_Resistance', 'Macro_Support', 'EMA_200_Macro']].copy()
    daily_walls.rename(columns={'Fecha': 'Date_Day'}, inplace=True)
    
    df_1h = pd.merge(df_1h, daily_walls, on='Date_Day', how='left')

    # 2. CALCULATE TOLERANCE ZONES
    df_1h['Dist_R'] = abs(df_1h['Maximo'] - df_1h['Macro_Resistance']) / df_1h['Macro_Resistance']
    df_1h['Dist_S'] = abs(df_1h['Minimo'] - df_1h['Macro_Support']) / df_1h['Macro_Support']
    
    df_1h['In_R_Zone'] = df_1h['Dist_R'] <= zone_margin
    df_1h['In_S_Zone'] = df_1h['Dist_S'] <= zone_margin

    # 3. EMA 50 AND STRUCTURE
    df_1h['EMA_50'] = df_1h['Cierre'].ewm(span=50, adjust=False).mean()
    df_1h['Local_Low'] = df_1h['Minimo'].shift(1).rolling(window=24).min()
    df_1h['Local_High'] = df_1h['Maximo'].shift(1).rolling(window=24).max()

    # 4. INSTITUTIONAL VOLUME FILTER
    df_1h['Vol_Avg_20'] = df_1h['Volumen'].rolling(window=20).mean()
    df_1h['High_Volume'] = df_1h['Volumen'] > df_1h['Vol_Avg_20']

    # 5. NEW: EXHAUSTION FILTER (RSI 14)
    delta = df_1h['Cierre'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss
    df_1h['RSI'] = 100 - (100 / (1 + rs))
    
    # We require that before falling, the price was hot (RSI > 55)
    df_1h['RSI_Short'] = df_1h['RSI'].shift(1) > 55 
    # We require that before rebounding, the price was exhausted (RSI < 45)
    df_1h['RSI_Long'] = df_1h['RSI'].shift(1) < 45 

    # 6. GATILLO CHoCH (Con Filtro de Tendencia Macro)
    tendencia_alcista = df_1h['Cierre'] > df_1h['EMA_200_Macro']
    tendencia_bajista = df_1h['Cierre'] < df_1h['EMA_200_Macro']

    df_1h['CHoCH_Bearish'] = df_1h['In_R_Zone'] & (df_1h['Cierre'] < df_1h['Local_Low']) & (df_1h['Cierre'] < df_1h['EMA_50']) & (df_1h['High_Volume'] | df_1h['RSI_Short']) & bearish_trend

    df_1h['CHoCH_Bullish'] = df_1h['In_S_Zone'] & (df_1h['Cierre'] > df_1h['Local_High']) & (df_1h['Cierre'] > df_1h['EMA_50']) & (df_1h['High_Volume'] | df_1h['RSI_Long']) & bullish_trend

    # 7. RECUPERAR EL FIBONACCI
    impulso = df_1h['Local_High'] - df_1h['Local_Low']
    df_1h['Fibo_33'] = df_1h['Local_Low'] + (impulso * 0.333)
    df_1h['Fibo_50'] = df_1h['Local_Low'] + (impulso * 0.500)
    df_1h['Fibo_66'] = df_1h['Local_Low'] + (impulso * 0.666)


    return df_1h