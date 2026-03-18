import pandas as pd


def identify_fvg(df, min_gap_pct=0.0, confirmation_type=None):
    """
    Identifies Fair Value Gaps (FVG) in an OHLC DataFrame with optional filters.

    Bullish FVG: low[i] > high[i-2]
    Bearish FVG: high[i] < low[i-2]

    Filters:
    - min_gap_pct: Minimum gap size as percentage of average price.
    - confirmation_type: 'ma' for moving average confirmation, 'volume' for volume.

    Returns a DataFrame with detected FVG.
    """
    fvg_list = []

    # Calculate moving averages if necessary
    if confirmation_type == 'ma':
        sma_close = df['Cierre'].rolling(20).mean()
    if confirmation_type == 'volume':
        sma_volume = df['Volumen'].rolling(20).mean()

    # We need at least 3 candles. Iterate from the third
    for i in range(2, len(df)):
        date = df['Fecha'].iloc[i]

        # Calculate average price for the gap
        avg_price = (df['Cierre'].iloc[i-2] + df['Cierre'].iloc[i-1] + df['Cierre'].iloc[i]) / 3

        # Bullish FVG: current candle low > high 2 candles ago
        if df['Minimo'].iloc[i] > df['Maximo'].iloc[i-2]:
            gap = df['Minimo'].iloc[i] - df['Maximo'].iloc[i-2]
            gap_pct = gap / avg_price if avg_price > 0 else 0

            if gap_pct >= min_gap_pct:
                # Confirmation
                confirm = True
                if confirmation_type == 'ma' and i >= 19:
                    confirm = df['Cierre'].iloc[i] > sma_close.iloc[i]
                elif confirmation_type == 'volume' and i >= 19:
                    confirm = df['Volumen'].iloc[i] > sma_volume.iloc[i] * 1.5

                if confirm:
                    fvg_list.append({
                        'Fecha': date,
                        'tipo': 'Bullish',
                        'FVG_Top': df['Minimo'].iloc[i],
                        'FVG_Bottom': df['Maximo'].iloc[i-2]
                    })

        # Bearish FVG: current candle high < low 2 candles ago
        elif df['Maximo'].iloc[i] < df['Minimo'].iloc[i-2]:
            gap = df['Minimo'].iloc[i-2] - df['Maximo'].iloc[i]
            gap_pct = gap / avg_price if avg_price > 0 else 0

            if gap_pct >= min_gap_pct:
                # Confirmation
                confirm = True
                if confirmation_type == 'ma' and i >= 19:
                    confirm = df['Cierre'].iloc[i] < sma_close.iloc[i]
                elif confirmation_type == 'volume' and i >= 19:
                    confirm = df['Volumen'].iloc[i] > sma_volume.iloc[i] * 1.5

                if confirm:
                    fvg_list.append({
                        'Fecha': date,
                        'tipo': 'Bearish',
                        'FVG_Top': df['Minimo'].iloc[i-2],
                        'FVG_Bottom': df['Maximo'].iloc[i]
                    })

    return pd.DataFrame(fvg_list)
