import pandas as pd

def calcular_tendencia_y_volumen(df):
    """
    Calcula la EMA 50, la media de volumen y el ratio de indecisión de las velas.
    """
    # 1. EMA de 50 periodos
    df['EMA_50'] = df['Cierre'].ewm(span=50, adjust=False).mean()

    # 2. Media Móvil Simple del Volumen (20 periodos)
    df['Volumen_SMA_20'] = df['Volumen'].rolling(window=20).mean()

    # 3. Indecisión: Ratio entre el cuerpo de la vela y su tamaño total
    tamano_vela = df['Maximo'] - df['Minimo']
    tamano_vela = tamano_vela.replace(0, 0.00001) # Trampa técnica para evitar el error de división por cero
    
    df['Cuerpo_Ratio'] = abs(df['Cierre'] - df['Apertura']) / tamano_vela

    return df