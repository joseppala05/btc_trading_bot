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