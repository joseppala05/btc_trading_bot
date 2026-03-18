import pandas as pd

# Añadimos el parámetro de comisión (0.1% por defecto)
def simular_mtf(df_1h, df_15m, ratio_riesgo_beneficio=3.0, margen_sl=0.003, comision_porcentaje=0.0002):
    resultados = []
    fecha_libre = pd.Timestamp('1970-01-01')

    df_15m['MA_15m'] = df_15m['Cierre'].rolling(window=10).mean() 

    setups = df_1h[(df_1h['CHoCH_Bajista'] == True) | (df_1h['CHoCH_Alcista'] == True)]

    for index, setup in setups.iterrows():
        if setup['Fecha'] <= fecha_libre:
            continue

        tipo = "SHORT" if setup['CHoCH_Bajista'] else "LONG"
        fecha_setup = setup['Fecha']
        fibo_33 = setup['Fibo_33']
        fibo_66 = setup['Fibo_66']
        
        sl_original = setup['Local_High'] * (1 + margen_sl) if tipo == "SHORT" else setup['Local_Low'] * (1 - margen_sl)

        velas_15m_futuro = df_15m[df_15m['Fecha'] > fecha_setup]
        estado = "ESPERANDO_FIBO"
        precio_entrada = sl = tp = riesgo = 0
        estado_proteccion = "NADA"

        for i_15m, vela_15m in velas_15m_futuro.iterrows():
            
            # FASE A
            if estado == "ESPERANDO_FIBO":
                if tipo == "SHORT" and vela_15m['Maximo'] >= fibo_33: estado = "GATILLO_ARMADO"
                elif tipo == "LONG" and vela_15m['Minimo'] <= fibo_66: estado = "GATILLO_ARMADO"
                    
                if (vela_15m['Fecha'] - fecha_setup).total_seconds() > 86400: break

            # FASE B
            elif estado == "GATILLO_ARMADO":
                if tipo == "SHORT" and vela_15m['Cierre'] < vela_15m['MA_15m']:
                    precio_entrada = vela_15m['Cierre']
                    sl = sl_original
                    riesgo = sl - precio_entrada
                    if riesgo <= 0: break
                    tp = precio_entrada - (riesgo * ratio_riesgo_beneficio)
                    estado = "EN_OPERACION"
                    
                elif tipo == "LONG" and vela_15m['Cierre'] > vela_15m['MA_15m']:
                    precio_entrada = vela_15m['Cierre']
                    sl = sl_original
                    riesgo = precio_entrada - sl
                    if riesgo <= 0: break
                    tp = precio_entrada + (riesgo * ratio_riesgo_beneficio)
                    estado = "EN_OPERACION"

            # FASE C: Gestión y Cálculo de Comisiones
            elif estado == "EN_OPERACION":
                
                # Trailing Stop Escalonado
                if tipo == "SHORT":
                    distancia_a_favor = precio_entrada - vela_15m['Minimo']
                    if distancia_a_favor >= (riesgo * 1.5) and estado_proteccion != "PROTEGIDO":
                        sl = precio_entrada - (riesgo * 0.5)
                        estado_proteccion = "PROTEGIDO"
                    elif distancia_a_favor >= riesgo and estado_proteccion == "NADA":
                        sl = precio_entrada
                        estado_proteccion = "BREAKEVEN"
                elif tipo == "LONG":
                    distancia_a_favor = vela_15m['Maximo'] - precio_entrada
                    if distancia_a_favor >= (riesgo * 1.5) and estado_proteccion != "PROTEGIDO":
                        sl = precio_entrada + (riesgo * 0.5)
                        estado_proteccion = "PROTEGIDO"
                    elif distancia_a_favor >= riesgo and estado_proteccion == "NADA":
                        sl = precio_entrada
                        estado_proteccion = "BREAKEVEN"

                # Comprobación de salidas y cálculo matemático de comisiones en R
                if tipo == "SHORT":
                    if vela_15m['Maximo'] >= sl:
                        precio_salida = sl
                        if estado_proteccion == "PROTEGIDO": res = "🔵 TP_PARCIAL (+0.5R)"
                        elif estado_proteccion == "BREAKEVEN": res = "⚪ BREAKEVEN"
                        else: res = "🔴 SL"
                        
                        # Fórmula: (Costo entrada + Costo salida) / Riesgo
                        comision_r = ((precio_entrada * comision_porcentaje) + (precio_salida * comision_porcentaje)) / riesgo
                        resultados.append({'Fecha_Setup': fecha_setup, 'Tipo': tipo, 'Entrada': round(precio_entrada,2), 'Resultado': res, 'Comision_R': round(comision_r, 3)})
                        fecha_libre = vela_15m['Fecha']
                        break
                        
                    elif vela_15m['Minimo'] <= tp:
                        precio_salida = tp
                        comision_r = ((precio_entrada * comision_porcentaje) + (precio_salida * comision_porcentaje)) / riesgo
                        resultados.append({'Fecha_Setup': fecha_setup, 'Tipo': tipo, 'Entrada': round(precio_entrada,2), 'Resultado': "🟢 TP FULL (+2R)", 'Comision_R': round(comision_r, 3)})
                        fecha_libre = vela_15m['Fecha']
                        break
                        
                else: # LONG
                    if vela_15m['Minimo'] <= sl:
                        precio_salida = sl
                        if estado_proteccion == "PROTEGIDO": res = "🔵 TP_PARCIAL (+0.5R)"
                        elif estado_proteccion == "BREAKEVEN": res = "⚪ BREAKEVEN"
                        else: res = "🔴 SL"
                        
                        comision_r = ((precio_entrada * comision_porcentaje) + (precio_salida * comision_porcentaje)) / riesgo
                        resultados.append({'Fecha_Setup': fecha_setup, 'Tipo': tipo, 'Entrada': round(precio_entrada,2), 'Resultado': res, 'Comision_R': round(comision_r, 3)})
                        fecha_libre = vela_15m['Fecha']
                        break
                        
                    elif vela_15m['Maximo'] >= tp:
                        precio_salida = tp
                        comision_r = ((precio_entrada * comision_porcentaje) + (precio_salida * comision_porcentaje)) / riesgo
                        resultados.append({'Fecha_Setup': fecha_setup, 'Tipo': tipo, 'Entrada': round(precio_entrada,2), 'Resultado': "🟢 TP FULL (+2R)", 'Comision_R': round(comision_r, 3)})
                        fecha_libre = vela_15m['Fecha']
                        break

    return pd.DataFrame(resultados)


def simular_fvg(
    df_1h,
    df_15m,
    ratio_riesgo_beneficio=2.0,
    margen_sl=0.01,
    comision_porcentaje=0.0002,
    usar_ma=True,
    ma_window=10,
    max_days_zone=7,
    min_gap_pct=0.002,
):
    """Simulación basada en zonas FVG (Fair Value Gap).

    - Genera zonas FVG en 1H.
    - Busca entrada en 15M cuando el precio vuelve a la zona.
    - Usa MA para confirmar dirección (opcional).
    """

    from indicators.fvg import detectar_fvg_zonas

    resultados = []
    fecha_libre = pd.Timestamp('1970-01-01')

    zonas = detectar_fvg_zonas(df_1h, min_gap_pct=min_gap_pct)
    if not zonas:
        return pd.DataFrame(resultados)

    if usar_ma:
        df_15m['MA_15m'] = df_15m['Cierre'].rolling(window=ma_window).mean()

    for zona in zonas:
        if zona['fecha'] <= fecha_libre:
            continue

        tipo = zona['tipo']
        fecha_inicio = zona['fecha']
        zona_low = zona['low']
        zona_high = zona['high']
        rango_zona = zona_high - zona_low

        # Stop loss justo fuera de la zona, con margen
        if tipo == 'LONG':
            sl_base = zona_low
            sl = sl_base - (rango_zona * margen_sl)
        else:
            sl_base = zona_high
            sl = sl_base + (rango_zona * margen_sl)

        precio_entrada = sl = tp = riesgo = 0
        en_operacion = False

        velas_15m_futuro = df_15m[df_15m['Fecha'] > fecha_inicio]
        for vela_15m in velas_15m_futuro.itertuples(index=False):
            if vela_15m.Fecha <= fecha_inicio:
                continue

            # Si la zona ha caducado, abandono
            if (vela_15m.Fecha - fecha_inicio).total_seconds() > max_days_zone * 86400:
                break

            if not en_operacion:
                # Buscamos que el cierre del 15m quede dentro de la zona (entrada en la FVG)
                entra_en_zona = zona_low <= vela_15m.Cierre <= zona_high
                if tipo == 'LONG':
                    confirmacion = vela_15m.Cierre > getattr(vela_15m, 'MA_15m', float('inf')) if usar_ma else True
                else:
                    confirmacion = vela_15m.Cierre < getattr(vela_15m, 'MA_15m', float('-inf')) if usar_ma else True

                if entra_en_zona and confirmacion:
                    precio_entrada = vela_15m.Cierre

                    # Recalculate SL usando la zona y el precio de entrada para asegurar que el riesgo sea positivo
                    margen_abs = max(rango_zona * margen_sl, abs(precio_entrada) * 0.0005)
                    if tipo == 'LONG':
                        sl = min(zona_low, precio_entrada) - margen_abs
                    else:
                        sl = max(zona_high, precio_entrada) + margen_abs

                    riesgo = abs(precio_entrada - sl)
                    if riesgo <= 0:
                        break

                    tp = (
                        precio_entrada + (riesgo * ratio_riesgo_beneficio)
                        if tipo == 'LONG'
                        else precio_entrada - (riesgo * ratio_riesgo_beneficio)
                    )
                    en_operacion = True
                    estado_proteccion = 'NADA'
                    continue

            # Si estamos en operación, gestionamos salida
            if en_operacion:
                if tipo == 'LONG':
                    # Trailing y breakeven rápido
                    distancia_a_favor = vela_15m.Maximo - precio_entrada
                    if distancia_a_favor >= (riesgo * 1.5) and estado_proteccion != 'PROTEGIDO':
                        sl = precio_entrada + (riesgo * 0.5)
                        estado_proteccion = 'PROTEGIDO'
                    elif distancia_a_favor >= riesgo and estado_proteccion == 'NADA':
                        sl = precio_entrada
                        estado_proteccion = 'BREAKEVEN'

                    if vela_15m.Minimo <= sl:
                        precio_salida = sl
                        if estado_proteccion == 'PROTEGIDO':
                            res = '🔵 TP_PARCIAL (+0.5R)'
                        elif estado_proteccion == 'BREAKEVEN':
                            res = '⚪ BREAKEVEN'
                        else:
                            res = '🔴 SL'

                        comision_r = ((precio_entrada * comision_porcentaje) + (precio_salida * comision_porcentaje)) / riesgo
                        resultados.append({
                            'Fecha_Setup': fecha_inicio,
                            'Tipo': tipo,
                            'Entrada': round(precio_entrada, 2),
                            'Resultado': res,
                            'Comision_R': round(comision_r, 3),
                        })
                        fecha_libre = vela_15m.Fecha
                        break

                    if vela_15m.Maximo >= tp:
                        precio_salida = tp
                        comision_r = ((precio_entrada * comision_porcentaje) + (precio_salida * comision_porcentaje)) / riesgo
                        resultados.append({
                            'Fecha_Setup': fecha_inicio,
                            'Tipo': tipo,
                            'Entrada': round(precio_entrada, 2),
                            'Resultado': '🟢 TP FULL (+2R)',
                            'Comision_R': round(comision_r, 3),
                        })
                        fecha_libre = vela_15m.Fecha
                        break

                else:  # SHORT
                    distancia_a_favor = precio_entrada - vela_15m.Minimo
                    if distancia_a_favor >= (riesgo * 1.5) and estado_proteccion != 'PROTEGIDO':
                        sl = precio_entrada - (riesgo * 0.5)
                        estado_proteccion = 'PROTEGIDO'
                    elif distancia_a_favor >= riesgo and estado_proteccion == 'NADA':
                        sl = precio_entrada
                        estado_proteccion = 'BREAKEVEN'

                    if vela_15m.Maximo >= sl:
                        precio_salida = sl
                        if estado_proteccion == 'PROTEGIDO':
                            res = '🔵 TP_PARCIAL (+0.5R)'
                        elif estado_proteccion == 'BREAKEVEN':
                            res = '⚪ BREAKEVEN'
                        else:
                            res = '🔴 SL'

                        comision_r = ((precio_entrada * comision_porcentaje) + (precio_salida * comision_porcentaje)) / riesgo
                        resultados.append({
                            'Fecha_Setup': fecha_inicio,
                            'Tipo': tipo,
                            'Entrada': round(precio_entrada, 2),
                            'Resultado': res,
                            'Comision_R': round(comision_r, 3),
                        })
                        fecha_libre = vela_15m.Fecha
                        break

                    if vela_15m.Minimo <= tp:
                        precio_salida = tp
                        comision_r = ((precio_entrada * comision_porcentaje) + (precio_salida * comision_porcentaje)) / riesgo
                        resultados.append({
                            'Fecha_Setup': fecha_inicio,
                            'Tipo': tipo,
                            'Entrada': round(precio_entrada, 2),
                            'Resultado': '🟢 TP FULL (+2R)',
                            'Comision_R': round(comision_r, 3),
                        })
                        fecha_libre = vela_15m.Fecha
                        break

    return pd.DataFrame(resultados)
