import pandas as pd

def simular_mtf(df_1h, df_15m, ratio_riesgo_beneficio=2.0):
    resultados = []
    fecha_libre = pd.Timestamp('1970-01-01')

    # 1. Preparar el gráfico de 15m (Media Móvil de 10 periodos)
    df_15m['MA_15m'] = df_15m['Cierre'].rolling(window=10).mean() 

    setups = df_1h[(df_1h['CHoCH_Bajista'] == True) | (df_1h['CHoCH_Alcista'] == True)]

    for index, setup in setups.iterrows():
        if setup['Fecha'] <= fecha_libre:
            continue

        tipo = "SHORT" if setup['CHoCH_Bajista'] else "LONG"
        fecha_setup = setup['Fecha']
        
        # IMPORTANTE: Ahora leemos los 3 niveles de Fibo
        fibo_33 = setup['Fibo_33']
        fibo_50 = setup['Fibo_50']
        fibo_66 = setup['Fibo_66']
        
        sl_original = setup['Local_High'] if tipo == "SHORT" else setup['Local_Low']

        # Anunciamos el Setup y la zona objetivo
        if tipo == "SHORT":
            print(f"\n[!] Setup {tipo} el {fecha_setup}. Esperando rebote al 1/3 Fibo ({fibo_33:.2f})...")
        else:
            print(f"\n[!] Setup {tipo} el {fecha_setup}. Esperando caída al 1/3 Fibo ({fibo_66:.2f})...")

        velas_15m_futuro = df_15m[df_15m['Fecha'] > fecha_setup]
        estado = "ESPERANDO_FIBO"
        precio_entrada = sl = tp = 0

        for i_15m, vela_15m in velas_15m_futuro.iterrows():
            
            # FASE A: Esperar entrar en la Zona de Fibo (1/3 de retroceso)
            if estado == "ESPERANDO_FIBO":
                if tipo == "SHORT" and vela_15m['Maximo'] >= fibo_33:
                    estado = "GATILLO_ARMADO"
                    print(f"  -> {vela_15m['Fecha']}: ¡Zona Fibo tocada! Esperando cruce MA bajista...")
                elif tipo == "LONG" and vela_15m['Minimo'] <= fibo_66:
                    estado = "GATILLO_ARMADO"
                    print(f"  -> {vela_15m['Fecha']}: ¡Zona Fibo tocada! Esperando cruce MA alcista...")
                    
                if (vela_15m['Fecha'] - fecha_setup).total_seconds() > 86400:
                    print("  -> Cancelado: Pasaron 24h sin tocar el Fibo.")
                    break

            # FASE B: Gatillo de 15 Minutos (Cruce de Media)
            elif estado == "GATILLO_ARMADO":
                if tipo == "SHORT" and vela_15m['Cierre'] < vela_15m['MA_15m']:
                    precio_entrada = vela_15m['Cierre']
                    sl = sl_original
                    riesgo = sl - precio_entrada
                    if riesgo <= 0: break
                    tp = precio_entrada - (riesgo * ratio_riesgo_beneficio)
                    estado = "EN_OPERACION"
                    print(f"  -> {vela_15m['Fecha']}: ¡DISPARO! Entrando en {precio_entrada:.2f}")
                    
                elif tipo == "LONG" and vela_15m['Cierre'] > vela_15m['MA_15m']:
                    precio_entrada = vela_15m['Cierre']
                    sl = sl_original
                    riesgo = precio_entrada - sl
                    if riesgo <= 0: break
                    tp = precio_entrada + (riesgo * ratio_riesgo_beneficio)
                    estado = "EN_OPERACION"
                    print(f"  -> {vela_15m['Fecha']}: ¡DISPARO! Entrando en {precio_entrada:.2f}")

            # FASE C: Gestión del Trade
            elif estado == "EN_OPERACION":
                if tipo == "SHORT":
                    if vela_15m['Maximo'] >= sl:
                        resultados.append({'Fecha_Setup': fecha_setup, 'Tipo': tipo, 'Entrada': round(precio_entrada,2), 'Resultado': "🔴 SL"})
                        fecha_libre = vela_15m['Fecha']
                        print(f"  -> {vela_15m['Fecha']}: Operación cerrada por Stop Loss.")
                        break
                    elif vela_15m['Minimo'] <= tp:
                        resultados.append({'Fecha_Setup': fecha_setup, 'Tipo': tipo, 'Entrada': round(precio_entrada,2), 'Resultado': "🟢 TP"})
                        fecha_libre = vela_15m['Fecha']
                        print(f"  -> {vela_15m['Fecha']}: Operación cerrada por Take Profit.")
                        break
                else: # LONG
                    if vela_15m['Minimo'] <= sl:
                        resultados.append({'Fecha_Setup': fecha_setup, 'Tipo': tipo, 'Entrada': round(precio_entrada,2), 'Resultado': "🔴 SL"})
                        fecha_libre = vela_15m['Fecha']
                        print(f"  -> {vela_15m['Fecha']}: Operación cerrada por Stop Loss.")
                        break
                    elif vela_15m['Maximo'] >= tp:
                        resultados.append({'Fecha_Setup': fecha_setup, 'Tipo': tipo, 'Entrada': round(precio_entrada,2), 'Resultado': "🟢 TP"})
                        fecha_libre = vela_15m['Fecha']
                        print(f"  -> {vela_15m['Fecha']}: Operación cerrada por Take Profit.")
                        break

    return pd.DataFrame(resultados)