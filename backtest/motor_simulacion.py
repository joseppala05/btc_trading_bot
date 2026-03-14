import pandas as pd

def simular_operaciones(df):
    """
    Simula el resultado de las señales generadas usando un RR de 1:1.5.
    """
    resultados = []
    
    # Filtramos para iterar solo sobre las velas donde hubo señal
    senales = df[df['Senal'] != 0]

    for index, row in senales.iterrows():
        tipo = "LONG" if row['Senal'] == 1 else "SHORT"
        entrada = row['Cierre']
        fecha_entrada = row['Fecha']

        # Calcular Stop Loss y Take Profit (Ratio 1:1.5)
        if tipo == "LONG":
            sl = row['Soporte_Activo']
            riesgo = entrada - sl
            if riesgo <= 0: continue # Evita errores matemáticos
            tp = entrada + (riesgo * 1.5)
        else: # SHORT
            sl = row['Resistencia_Activa']
            riesgo = sl - entrada
            if riesgo <= 0: continue
            tp = entrada - (riesgo * 1.5)

        # "Viajar al futuro": Recortamos la tabla desde la vela siguiente a la entrada
        velas_futuras = df.loc[index + 1:]
        resultado_operacion = "ABIERTA" # Por si el histórico termina y no ha tocado nada

        # Comprobamos vela a vela qué nivel toca primero el precio
        for f_index, f_row in velas_futuras.iterrows():
            if tipo == "LONG":
                if f_row['Minimo'] <= sl:
                    resultado_operacion = "🔴 PERDIDA (SL)"
                    break
                elif f_row['Maximo'] >= tp:
                    resultado_operacion = "🟢 GANANCIA (TP)"
                    break
            else: # SHORT
                if f_row['Maximo'] >= sl:
                    resultado_operacion = "🔴 PERDIDA (SL)"
                    break
                elif f_row['Minimo'] <= tp:
                    resultado_operacion = "🟢 GANANCIA (TP)"
                    break

        # Guardamos el resultado de esta operación
        resultados.append({
            'Fecha': fecha_entrada,
            'Tipo': tipo,
            'Entrada': round(entrada, 2),
            'SL': round(sl, 2),
            'TP': round(tp, 2),
            'Resultado': resultado_operacion
        })

    # Devolvemos un DataFrame limpio con los resultados finales
    return pd.DataFrame(resultados)