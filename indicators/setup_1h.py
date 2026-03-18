import pandas as pd
import numpy as np

def analizar_setup_1h(df_1h, df_1d, margen_zona=0.05):
    # 1. SINCRONIZAR RELOJES
    df_1h['Fecha_Dia'] = df_1h['Fecha'].dt.floor('d')
    muros_diarios = df_1d[['Fecha', 'Resistencia_Macro', 'Soporte_Macro', 'EMA_200_Macro']].copy()
    muros_diarios.rename(columns={'Fecha': 'Fecha_Dia'}, inplace=True)
    
    df_1h = pd.merge(df_1h, muros_diarios, on='Fecha_Dia', how='left')

    # 2. CALCULAR ZONAS DE TOLERANCIA
    df_1h['Distancia_R'] = abs(df_1h['Maximo'] - df_1h['Resistencia_Macro']) / df_1h['Resistencia_Macro']
    df_1h['Distancia_S'] = abs(df_1h['Minimo'] - df_1h['Soporte_Macro']) / df_1h['Soporte_Macro']
    
    df_1h['En_Zona_R'] = df_1h['Distancia_R'] <= margen_zona
    df_1h['En_Zona_S'] = df_1h['Distancia_S'] <= margen_zona

    # 3. EMA 50 Y ESTRUCTURA
    df_1h['EMA_50'] = df_1h['Cierre'].ewm(span=50, adjust=False).mean()
    df_1h['Local_Low'] = df_1h['Minimo'].shift(1).rolling(window=24).min()
    df_1h['Local_High'] = df_1h['Maximo'].shift(1).rolling(window=24).max()

    # 4. FILTRO DE VOLUMEN INSTITUCIONAL
    df_1h['Vol_Media_20'] = df_1h['Volumen'].rolling(window=20).mean()
    df_1h['Volumen_Alto'] = df_1h['Volumen'] > df_1h['Vol_Media_20']

    # 5. NUEVO: FILTRO DE AGOTAMIENTO (RSI 14)
    delta = df_1h['Cierre'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss
    df_1h['RSI'] = 100 - (100 / (1 + rs))
    
    # Exigimos que antes de caer, el precio estuviera caliente (RSI > 55)
    df_1h['RSI_Corto'] = df_1h['RSI'].shift(1) > 55 
    # Exigimos que antes de rebotar, el precio estuviera agotado (RSI < 45)
    df_1h['RSI_Largo'] = df_1h['RSI'].shift(1) < 45 

    # 6. GATILLO CHoCH (Con Filtro de Tendencia Macro)
    tendencia_alcista = df_1h['Cierre'] > df_1h['EMA_200_Macro']
    tendencia_bajista = df_1h['Cierre'] < df_1h['EMA_200_Macro']

    df_1h['CHoCH_Bajista'] = df_1h['En_Zona_R'] & (df_1h['Cierre'] < df_1h['Local_Low']) & (df_1h['Cierre'] < df_1h['EMA_50']) & (df_1h['Volumen_Alto'] | df_1h['RSI_Corto']) & tendencia_bajista

    df_1h['CHoCH_Alcista'] = df_1h['En_Zona_S'] & (df_1h['Cierre'] > df_1h['Local_High']) & (df_1h['Cierre'] > df_1h['EMA_50']) & (df_1h['Volumen_Alto'] | df_1h['RSI_Largo']) & tendencia_alcista

    # 7. RECUPERAR EL FIBONACCI
    impulso = df_1h['Local_High'] - df_1h['Local_Low']
    df_1h['Fibo_33'] = df_1h['Local_Low'] + (impulso * 0.333)
    df_1h['Fibo_50'] = df_1h['Local_Low'] + (impulso * 0.500)
    df_1h['Fibo_66'] = df_1h['Local_Low'] + (impulso * 0.666)


    return df_1h