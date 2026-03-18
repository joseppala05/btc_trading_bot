import pandas as pd

# Add commission parameter (0.1% by default)
def simulate_mtf(df_1h, df_15m, risk_reward_ratio=3.0, sl_margin=0.003, commission_percentage=0.0002):
    results = []
    free_date = pd.Timestamp('1970-01-01')

    df_15m['MA_15m'] = df_15m['Cierre'].rolling(window=10).mean() 

    setups = df_1h[(df_1h['CHoCH_Bajista'] == True) | (df_1h['CHoCH_Alcista'] == True)]

    for index, setup in setups.iterrows():
        if setup['Fecha'] <= free_date:
            continue

        trade_type = "SHORT" if setup['CHoCH_Bajista'] else "LONG"
        setup_date = setup['Fecha']
        fibo_33 = setup['Fibo_33']
        fibo_66 = setup['Fibo_66']
        
        sl_original = setup['Local_High'] * (1 + sl_margin) if trade_type == "SHORT" else setup['Local_Low'] * (1 - sl_margin)

        velas_15m_futuro = df_15m[df_15m['Fecha'] > setup_date]
        state = "WAITING_FOR_FIBO"
        entry_price = sl = tp = risk = 0
        protection_state = "NOTHING"

        for i_15m, vela_15m in velas_15m_futuro.iterrows():
            
            # PHASE A
            if state == "WAITING_FOR_FIBO":
                if trade_type == "SHORT" and vela_15m['Maximo'] >= fibo_33: state = "TRIGGER_ARMED"
                elif trade_type == "LONG" and vela_15m['Minimo'] <= fibo_66: state = "TRIGGER_ARMED"
                    
                if (vela_15m['Fecha'] - setup_date).total_seconds() > 86400: break

            # PHASE B
            elif state == "TRIGGER_ARMED":
                if trade_type == "SHORT" and vela_15m['Cierre'] < vela_15m['MA_15m']:
                    entry_price = vela_15m['Cierre']
                    sl = sl_original
                    risk = sl - entry_price
                    if risk <= 0: break
                    tp = entry_price - (risk * risk_reward_ratio)
                    state = "IN_OPERATION"
                    
                elif trade_type == "LONG" and vela_15m['Cierre'] > vela_15m['MA_15m']:
                    entry_price = vela_15m['Cierre']
                    sl = sl_original
                    risk = entry_price - sl
                    if risk <= 0: break
                    tp = entry_price + (risk * risk_reward_ratio)
                    state = "IN_OPERATION"

            # PHASE C: Management and Commission Calculation
            elif state == "IN_OPERATION":
                
                # Trailing Stop Staggered
                if trade_type == "SHORT":
                    distance_in_favor = entry_price - vela_15m['Minimo']
                    if distance_in_favor >= (risk * 1.5) and protection_state != "PROTECTED":
                        sl = entry_price - (risk * 0.5)
                        protection_state = "PROTECTED"
                    elif distance_in_favor >= risk and protection_state == "NOTHING":
                        sl = entry_price
                        protection_state = "BREAKEVEN"
                elif trade_type == "LONG":
                    distance_in_favor = vela_15m['Maximo'] - entry_price
                    if distance_in_favor >= (risk * 1.5) and protection_state != "PROTECTED":
                        sl = entry_price + (risk * 0.5)
                        protection_state = "PROTECTED"
                    elif distance_in_favor >= risk and protection_state == "NOTHING":
                        sl = entry_price
                        protection_state = "BREAKEVEN"

                # Exit checks and mathematical commission calculation in R
                if trade_type == "SHORT":
                    if vela_15m['Maximo'] >= sl:
                        exit_price = sl
                        if protection_state == "PROTECTED": res = "🔵 TP_PARTIAL (+0.5R)"
                        elif protection_state == "BREAKEVEN": res = "⚪ BREAKEVEN"
                        else: res = "🔴 SL"
                        
                        # Formula: (Entry cost + Exit cost) / Risk
                        commission_r = ((entry_price * commission_percentage) + (exit_price * commission_percentage)) / risk
                        results.append({'Fecha_Setup': setup_date, 'Tipo': trade_type, 'Entrada': round(entry_price,2), 'Resultado': res, 'Comision_R': round(commission_r, 3)})
                        free_date = vela_15m['Fecha']
                        break
                        
                    elif vela_15m['Minimo'] <= tp:
                        exit_price = tp
                        commission_r = ((entry_price * commission_percentage) + (exit_price * commission_percentage)) / risk
                        results.append({'Fecha_Setup': setup_date, 'Tipo': trade_type, 'Entrada': round(entry_price,2), 'Resultado': "🟢 TP FULL (+2R)", 'Comision_R': round(commission_r, 3)})
                        free_date = vela_15m['Fecha']
                        break
                        
                else: # LONG
                    if vela_15m['Minimo'] <= sl:
                        exit_price = sl
                        if protection_state == "PROTECTED": res = "🔵 TP_PARTIAL (+0.5R)"
                        elif protection_state == "BREAKEVEN": res = "⚪ BREAKEVEN"
                        else: res = "🔴 SL"
                        
                        commission_r = ((entry_price * commission_percentage) + (exit_price * commission_percentage)) / risk
                        results.append({'Fecha_Setup': setup_date, 'Tipo': trade_type, 'Entrada': round(entry_price,2), 'Resultado': res, 'Comision_R': round(commission_r, 3)})
                        free_date = vela_15m['Fecha']
                        break
                        
                    elif vela_15m['Maximo'] >= tp:
                        exit_price = tp
                        commission_r = ((entry_price * commission_percentage) + (exit_price * commission_percentage)) / risk
                        results.append({'Fecha_Setup': setup_date, 'Tipo': trade_type, 'Entrada': round(entry_price,2), 'Resultado': "🟢 TP FULL (+2R)", 'Comision_R': round(commission_r, 3)})
                        free_date = vela_15m['Fecha']
                        break

    return pd.DataFrame(results)


def simulate_fvg(
    df_1h,
    df_15m,
    risk_reward_ratio=2.0,
    sl_margin=0.01,
    commission_percentage=0.0002,
    use_ma=True,
    ma_window=10,
    max_days_zone=7,
    min_gap_pct=0.002,
):
    """Simulation based on FVG (Fair Value Gap) zones.

    - Generates FVG zones in 1H.
    - Looks for entry in 15M when price returns to the zone.
    - Uses MA to confirm direction (optional).
    """

    from indicators.fvg import detectar_fvg_zonas

    results = []
    free_date = pd.Timestamp('1970-01-01')

    zones = detectar_fvg_zonas(df_1h, min_gap_pct=min_gap_pct)
    if not zones:
        return pd.DataFrame(results)

    if use_ma:
        df_15m['MA_15m'] = df_15m['Cierre'].rolling(window=ma_window).mean()

    for zona in zones:
        if zona['fecha'] <= free_date:
            continue

        trade_type = zona['tipo']
        start_date = zona['fecha']
        zone_low = zona['low']
        zone_high = zona['high']
        zone_range = zone_high - zone_low

        # Stop loss just outside the zone, with margin
        if trade_type == 'LONG':
            sl_base = zone_low
            sl = sl_base - (zone_range * sl_margin)
        else:
            sl_base = zone_high
            sl = sl_base + (zone_range * sl_margin)

        entry_price = sl = tp = risk = 0
        in_operation = False

        velas_15m_futuro = df_15m[df_15m['Fecha'] > start_date]
        for vela_15m in velas_15m_futuro.itertuples(index=False):
            if vela_15m.Fecha <= start_date:
                continue

            # If the zone has expired, abandon
            if (vela_15m.Fecha - start_date).total_seconds() > max_days_zone * 86400:
                break

            if not in_operation:
                # We look for the 15m close to be within the zone (entry in the FVG)
                enters_zone = zone_low <= vela_15m.Cierre <= zone_high
                if trade_type == 'LONG':
                    confirmation = vela_15m.Cierre > getattr(vela_15m, 'MA_15m', float('inf')) if use_ma else True
                else:
                    confirmation = vela_15m.Cierre < getattr(vela_15m, 'MA_15m', float('-inf')) if use_ma else True

                if enters_zone and confirmation:
                    entry_price = vela_15m.Cierre

                    # Recalculate SL using the zone and entry price to ensure positive risk
                    margin_abs = max(zone_range * sl_margin, abs(entry_price) * 0.0005)
                    if trade_type == 'LONG':
                        sl = min(zone_low, entry_price) - margin_abs
                    else:
                        sl = max(zone_high, entry_price) + margin_abs

                    risk = abs(entry_price - sl)
                    if risk <= 0:
                        break

                    tp = (
                        entry_price + (risk * risk_reward_ratio)
                        if trade_type == 'LONG'
                        else entry_price - (risk * risk_reward_ratio)
                    )
                    in_operation = True
                    protection_state = 'NOTHING'
                    continue

            # If we are in operation, manage exit
            if in_operation:
                if trade_type == 'LONG':
                    # Trailing and fast breakeven
                    distance_in_favor = vela_15m.Maximo - entry_price
                    if distance_in_favor >= (risk * 1.5) and protection_state != 'PROTECTED':
                        sl = entry_price + (risk * 0.5)
                        protection_state = 'PROTECTED'
                    elif distance_in_favor >= risk and protection_state == 'NOTHING':
                        sl = entry_price
                        protection_state = 'BREAKEVEN'

                    if vela_15m.Minimo <= sl:
                        exit_price = sl
                        if protection_state == 'PROTECTED':
                            res = '🔵 TP_PARTIAL (+0.5R)'
                        elif protection_state == 'BREAKEVEN':
                            res = '⚪ BREAKEVEN'
                        else:
                            res = '🔴 SL'

                        commission_r = ((entry_price * commission_percentage) + (exit_price * commission_percentage)) / risk
                        results.append({
                            'Fecha_Setup': start_date,
                            'Tipo': trade_type,
                            'Entrada': round(entry_price, 2),
                            'Resultado': res,
                            'Comision_R': round(commission_r, 3),
                        })
                        free_date = vela_15m.Fecha
                        break

                    if vela_15m.Maximo >= tp:
                        exit_price = tp
                        commission_r = ((entry_price * commission_percentage) + (exit_price * commission_percentage)) / risk
                        results.append({
                            'Fecha_Setup': start_date,
                            'Tipo': trade_type,
                            'Entrada': round(entry_price, 2),
                            'Resultado': '🟢 TP FULL (+2R)',
                            'Comision_R': round(commission_r, 3),
                        })
                        free_date = vela_15m.Fecha
                        break

                else:  # SHORT
                    distance_in_favor = entry_price - vela_15m.Minimo
                    if distance_in_favor >= (risk * 1.5) and protection_state != 'PROTECTED':
                        sl = entry_price - (risk * 0.5)
                        protection_state = 'PROTECTED'
                    elif distance_in_favor >= risk and protection_state == 'NOTHING':
                        sl = entry_price
                        protection_state = 'BREAKEVEN'

                    if vela_15m.Maximo >= sl:
                        exit_price = sl
                        if protection_state == 'PROTECTED':
                            res = '🔵 TP_PARTIAL (+0.5R)'
                        elif protection_state == 'BREAKEVEN':
                            res = '⚪ BREAKEVEN'
                        else:
                            res = '🔴 SL'

                        commission_r = ((entry_price * commission_percentage) + (exit_price * commission_percentage)) / risk
                        results.append({
                            'Fecha_Setup': start_date,
                            'Tipo': trade_type,
                            'Entrada': round(entry_price, 2),
                            'Resultado': res,
                            'Comision_R': round(commission_r, 3),
                        })
                        free_date = vela_15m.Fecha
                        break

                    if vela_15m.Minimo <= tp:
                        exit_price = tp
                        commission_r = ((entry_price * commission_percentage) + (exit_price * commission_percentage)) / risk
                        results.append({
                            'Fecha_Setup': start_date,
                            'Tipo': trade_type,
                            'Entrada': round(entry_price, 2),
                            'Resultado': '🟢 TP FULL (+2R)',
                            'Comision_R': round(commission_r, 3),
                        })
                        free_date = vela_15m.Fecha
                        break

    return pd.DataFrame(results)
