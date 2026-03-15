import pandas as pd

def analizar_macro_1d(df_1d, ventana=5):
    """
    Analiza el gráfico diario para encontrar S/R institucionales y
    confirmar rupturas reales usando la regla de las 2 velas.
    """
    window_size = (ventana * 2) + 1

    # --- 1. IDENTIFICAR MUROS (Soportes y Resistencias Macro) ---
    rolling_max = df_1d['Maximo'].rolling(window=window_size, center=True).max()
    rolling_min = df_1d['Minimo'].rolling(window=window_size, center=True).min()

    df_1d['Pivote_R'] = df_1d['Maximo'].where(df_1d['Maximo'] == rolling_max)
    df_1d['Pivote_S'] = df_1d['Minimo'].where(df_1d['Minimo'] == rolling_min)

    # Arrastramos el nivel confirmado hacia el futuro
    df_1d['Resistencia_Macro'] = df_1d['Pivote_R'].shift(ventana).ffill()
    df_1d['Soporte_Macro'] = df_1d['Pivote_S'].shift(ventana).ffill()

    df_1d.drop(columns=['Pivote_R', 'Pivote_S'], inplace=True)

    # --- 2. REGLA DE RUPTURA CONFIRMADA (2 VELAS) ---
    
    # Ruptura de Resistencia (Alcista)
    # Vela T-1 cierra por encima de la R
    rompe_r_ayer = df_1d['Cierre'].shift(1) > df_1d['Resistencia_Macro'].shift(1)
    # Vela T cierra por encima de la R
    confirma_r_hoy = df_1d['Cierre'] > df_1d['Resistencia_Macro']
    
    df_1d['R_Rota'] = rompe_r_ayer & confirma_r_hoy

    # Ruptura de Soporte (Bajista)
    # Vela T-1 cierra por debajo del S
    rompe_s_ayer = df_1d['Cierre'].shift(1) < df_1d['Soporte_Macro'].shift(1)
    # Vela T cierra por debajo del S
    confirma_s_hoy = df_1d['Cierre'] < df_1d['Soporte_Macro']
    
    df_1d['S_Roto'] = rompe_s_ayer & confirma_s_hoy

    return df_1d