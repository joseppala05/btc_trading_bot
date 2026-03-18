import pandas as pd


def identificar_fvg(df, min_gap_pct=0.0, confirmation_type=None):
    """
    Identifica Fair Value Gaps (FVG) en un DataFrame OHLC con filtros opcionales.

    FVG Alcista: low[i] > high[i-2]
    FVG Bajista: high[i] < low[i-2]

    Filtros:
    - min_gap_pct: Mínimo tamaño del gap como porcentaje del precio promedio.
    - confirmation_type: 'ma' para confirmación con media móvil, 'volume' para volumen.

    Retorna un DataFrame con los FVG detectados.
    """
    fvg_list = []

    # Calcular medias móviles si es necesario
    if confirmation_type == 'ma':
        sma_close = df['Cierre'].rolling(20).mean()
    if confirmation_type == 'volume':
        sma_volume = df['Volumen'].rolling(20).mean()

    # Necesitamos al menos 3 velas. Iteramos a partir de la tercera
    for i in range(2, len(df)):
        fecha = df['Fecha'].iloc[i]

        # Calcular precio promedio para el gap
        avg_price = (df['Cierre'].iloc[i-2] + df['Cierre'].iloc[i-1] + df['Cierre'].iloc[i]) / 3

        # FVG Alcista: bajo de vela actual > alto de vela hace 2
        if df['Minimo'].iloc[i] > df['Maximo'].iloc[i-2]:
            gap = df['Minimo'].iloc[i] - df['Maximo'].iloc[i-2]
            gap_pct = gap / avg_price if avg_price > 0 else 0

            if gap_pct >= min_gap_pct:
                # Confirmación
                confirm = True
                if confirmation_type == 'ma' and i >= 19:
                    confirm = df['Cierre'].iloc[i] > sma_close.iloc[i]
                elif confirmation_type == 'volume' and i >= 19:
                    confirm = df['Volumen'].iloc[i] > sma_volume.iloc[i] * 1.5

                if confirm:
                    fvg_list.append({
                        'Fecha': fecha,
                        'tipo': 'Bullish',
                        'FVG_Top': df['Minimo'].iloc[i],
                        'FVG_Bottom': df['Maximo'].iloc[i-2]
                    })

        # FVG Bajista: alto de vela actual < bajo de vela hace 2
        elif df['Maximo'].iloc[i] < df['Minimo'].iloc[i-2]:
            gap = df['Minimo'].iloc[i-2] - df['Maximo'].iloc[i]
            gap_pct = gap / avg_price if avg_price > 0 else 0

            if gap_pct >= min_gap_pct:
                # Confirmación
                confirm = True
                if confirmation_type == 'ma' and i >= 19:
                    confirm = df['Cierre'].iloc[i] < sma_close.iloc[i]
                elif confirmation_type == 'volume' and i >= 19:
                    confirm = df['Volumen'].iloc[i] > sma_volume.iloc[i] * 1.5

                if confirm:
                    fvg_list.append({
                        'Fecha': fecha,
                        'tipo': 'Bearish',
                        'FVG_Top': df['Minimo'].iloc[i-2],
                        'FVG_Bottom': df['Maximo'].iloc[i]
                    })

    return pd.DataFrame(fvg_list)
