import pandas as pd

def analizar_setup_1h(df_1h, df_1d, margen_zona=0.015):
    """
    Sincroniza el contexto Diario con 1H.
    Busca el CHoCH, la ruptura de EMA 50 y calcula los niveles Fibonacci
    SOLO cuando el precio está en la ZONA de un muro institucional.
    """
    # 1. SINCRONIZAR RELOJES (Inyectar Muros Diarios en la tabla de 1H)
    df_1h['Fecha_Dia'] = df_1h['Fecha'].dt.floor('d')
    muros_diarios = df_1d[['Fecha', 'Resistencia_Macro', 'Soporte_Macro']].copy()
    muros_diarios.rename(columns={'Fecha': 'Fecha_Dia'}, inplace=True)
    
    df_1h = pd.merge(df_1h, muros_diarios, on='Fecha_Dia', how='left')

    # 2. CALCULAR ZONAS DE TOLERANCIA
    df_1h['Distancia_R'] = abs(df_1h['Maximo'] - df_1h['Resistencia_Macro']) / df_1h['Resistencia_Macro']
    df_1h['Distancia_S'] = abs(df_1h['Minimo'] - df_1h['Soporte_Macro']) / df_1h['Soporte_Macro']
    
    df_1h['En_Zona_R'] = df_1h['Distancia_R'] <= margen_zona
    df_1h['En_Zona_S'] = df_1h['Distancia_S'] <= margen_zona

    # 3. EMA 50 Y ESTRUCTURA
    df_1h['EMA_50'] = df_1h['Cierre'].ewm(span=50, adjust=False).mean()
    
    # Suelos y Techos locales (mínimo y máximo de las últimas 10 horas)
    df_1h['Local_Low'] = df_1h['Minimo'].shift(1).rolling(window=10).min()
    df_1h['Local_High'] = df_1h['Maximo'].shift(1).rolling(window=10).max()

    # 4. GATILLO CHoCH
    df_1h['CHoCH_Bajista'] = df_1h['En_Zona_R'] & (df_1h['Cierre'] < df_1h['Local_Low']) & (df_1h['Cierre'] < df_1h['EMA_50'])
    df_1h['CHoCH_Alcista'] = df_1h['En_Zona_S'] & (df_1h['Cierre'] > df_1h['Local_High']) & (df_1h['Cierre'] > df_1h['EMA_50'])

    # 5. RECUPERAR EL FIBONACCI (Niveles de Pullback)
    impulso = df_1h['Local_High'] - df_1h['Local_Low']
    df_1h['Fibo_33'] = df_1h['Local_Low'] + (impulso * 0.333)
    df_1h['Fibo_50'] = df_1h['Local_Low'] + (impulso * 0.500)
    df_1h['Fibo_66'] = df_1h['Local_Low'] + (impulso * 0.666)

    return df_1h