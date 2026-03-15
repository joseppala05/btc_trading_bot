import pandas as pd
import numpy as np

def generar_position(df, margen_tolerancia=0.003):
    """
    Evalúa las reglas de la estrategia y genera una columna 'Senal':
    1 = LONG, -1 = SHORT, 0 = NADA.
    """
    # 1. Calcular a qué distancia porcentual está el precio de los S/R activos
    distancia_resistencia = abs(df['Maximo'] - df['Resistencia_Activa']) / df['Resistencia_Activa']
    distancia_soporte = abs(df['Minimo'] - df['Soporte_Activo']) / df['Soporte_Activo']

    # 2. Confirmar la Desaceleración (Indecisión + Bajo Volumen)
    indecision = (df['Cuerpo_Ratio'] < 0.3)
    bajo_volumen = (df['Volumen'] < df['Volumen_SMA_20'])
    desaceleracion = indecision & bajo_volumen

    # 3. Gatillo LONG (Soporte + Desaceleración + Tendencia alcista en 1H)
    condicion_long = (distancia_soporte <= margen_tolerancia) & desaceleracion & (df['Cierre'] > df['EMA_50'])

    # 4. Gatillo SHORT (Resistencia + Desaceleración + Tendencia bajista en 1H)
    condicion_short = (distancia_resistencia <= margen_tolerancia) & desaceleracion & (df['Cierre'] < df['EMA_50'])

    # 5. Inyectar la señal en la tabla de forma vectorizada
    condiciones = [condicion_long, condicion_short]
    valores = [1, -1]
    df['Senal'] = np.select(condiciones, valores, default=0)

    return df