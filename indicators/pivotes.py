import pandas as pd

def calcular_pivotes(df, ventana=5):
    """
    Identifica pivotes locales (Soportes y Resistencias).
    ventana: Número de velas a izquierda y derecha para confirmar el pivote.
    """
    window_size = (ventana * 2) + 1

    # 1. Buscamos el máximo y mínimo en una ventana centrada
    rolling_max = df['Maximo'].rolling(window=window_size, center=True).max()
    rolling_min = df['Minimo'].rolling(window=window_size, center=True).min()

    # 2. Marcamos el precio exacto donde ocurrió el pivote (y ponemos NaN donde no hay)
    df['Pivote_R'] = df['Maximo'].where(df['Maximo'] == rolling_max)
    df['Pivote_S'] = df['Minimo'].where(df['Minimo'] == rolling_min)

    # 3. EL PASO CRÍTICO: Confirmación en tiempo real.
    # Desplazamos el resultado 'ventana' velas hacia abajo (porque tardamos 5h en confirmarlo)
    # y arrastramos el valor hacia el futuro (Forward Fill) para mantener la línea de S/R activa.
    df['Resistencia_Activa'] = df['Pivote_R'].shift(ventana).ffill()
    df['Soporte_Activo'] = df['Pivote_S'].shift(ventana).ffill()

    # Limpiamos las columnas temporales para no ensuciar la tabla
    df.drop(columns=['Pivote_R', 'Pivote_S'], inplace=True)

    return df