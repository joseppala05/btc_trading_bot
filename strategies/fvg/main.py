"""Estrategia basada en Fair Value Gaps (FVG).

Detecta FVG en timeframe de 1H y entra en reversiones cuando el precio toca el borde del FVG en 15M.
"""

import os
import sys

import pandas as pd

from backtest.motor_simulacion import simular_mtf
from indicators.fvg import identificar_fvg

# Aseguramos que los emojis y símbolos se impriman bien en Windows PowerShell.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def run(activos=None, ratio_riesgo_beneficio=2.0, margen_sl=0.01, min_gap_pct=0.01, confirmation_type='volume'):
    activos = activos or ['btc']
    todos_los_resultados = []

    print("Iniciando Backtest FVG Multi-Moneda...")
    for activo in activos:
        print(f"\n[>] Analizando {activo.upper()}...")

        # 1. Cargar tablas
        df_1h = pd.read_csv(os.path.join('data', f'{activo}_1h.csv'), parse_dates=['Fecha'])
        df_15m = pd.read_csv(os.path.join('data', f'{activo}_15m.csv'), parse_dates=['Fecha'])

        # 2. Identificar FVG en 1H
        fvgs = identificar_fvg(df_1h, min_gap_pct=min_gap_pct, confirmation_type=confirmation_type)
        print(f"   -> FVG detectados: {len(fvgs)}")

        # 3. Simular entradas en 15M basadas en FVG
        df_resultados = simular_fvg(df_1h, df_15m, fvgs, ratio_riesgo_beneficio, margen_sl)

        if not df_resultados.empty:
            df_resultados.insert(0, 'Activo', activo.upper())
            todos_los_resultados.append(df_resultados)

    # --- UNIR TODOS LOS RESULTADOS ---
    if todos_los_resultados:
        reporte_final = pd.concat(todos_los_resultados, ignore_index=True)
        reporte_final = reporte_final.sort_values(by='Fecha_Setup')

        print("\n\n============================================================")
        print("      PORTAFOLIO GLOBAL FVG (BTC + ETH + SOL + XRP + ADA) ")
        print("============================================================")
        print(reporte_final.to_string(index=False))

        total = len(reporte_final)
        ganadas_full = len(reporte_final[reporte_final['Resultado'].str.startswith("🟢 TP")])
        perdidas = len(reporte_final[reporte_final['Resultado'] == "🔴 SL"])

        total_victorias = ganadas_full
        operaciones_validas = total
        win_rate = (total_victorias / operaciones_validas) * 100 if operaciones_validas > 0 else 0

        ganancia_bruta_r = reporte_final['R'].sum()
        comisiones_totales_r = reporte_final['Comision_R'].sum()
        ganancia_neta_r = ganancia_bruta_r - comisiones_totales_r

        print(f"\n--- ESTADÍSTICAS DEL PORTAFOLIO TOTAL (2024-2026) ---")
        print(f"Total Operaciones Globales: {total}")
        print(f"Victorias Totales: {total_victorias}")
        print(f"Perdidas (-1R): {perdidas}")
        print(f"Win Rate Efectivo: {win_rate:.2f}%")
        print(f"Coste Total en Comisiones: -{comisiones_totales_r:.2f}R")
        print(f"\n>>> BENEFICIO NETO REAL (Tras Comisiones): {ganancia_neta_r:+.2f}R <<<")
    else:
        print("\nNo se completó ninguna operación en todo el portafolio.")


def simular_fvg(df_1h, df_15m, fvgs, ratio_riesgo_beneficio=2.0, margen_sl=0.01):
    """
    Simula entradas basadas en FVG detectados en 1H, esperando toques en 15M.
    """
    resultados = []
    fecha_libre = pd.Timestamp('1970-01-01')

    for _, fvg in fvgs.iterrows():
        if fvg['Fecha'] <= fecha_libre:
            continue

        tipo = "LONG" if fvg['tipo'] == 'Bullish' else "SHORT"
        fecha_setup = fvg['Fecha']
        fvg_top = fvg['FVG_Top']
        fvg_bottom = fvg['FVG_Bottom']

        # Zona de entrada: borde del FVG
        zona_entrada = fvg_bottom if tipo == "LONG" else fvg_top

        # TP en el otro lado del FVG
        tp_fvg = fvg_top if tipo == "LONG" else fvg_bottom

        velas_15m_futuro = df_15m[df_15m['Fecha'] > fecha_setup]
        estado = "ESPERANDO_TOQUE"
        precio_entrada = sl = tp = riesgo = 0

        for i_15m, vela_15m in velas_15m_futuro.iterrows():
            if estado == "ESPERANDO_TOQUE":
                # Entrar si toca la zona (para LONG: precio baja a zona, para SHORT: sube a zona)
                if tipo == "LONG" and vela_15m['Minimo'] <= zona_entrada:
                    precio_entrada = zona_entrada
                    sl = precio_entrada * (1 - margen_sl)
                    riesgo = precio_entrada - sl
                    if riesgo <= 0: break
                    tp = tp_fvg
                    estado = "EN_OPERACION"
                elif tipo == "SHORT" and vela_15m['Maximo'] >= zona_entrada:
                    precio_entrada = zona_entrada
                    sl = precio_entrada * (1 + margen_sl)
                    riesgo = sl - precio_entrada
                    if riesgo <= 0: break
                    tp = tp_fvg
                    estado = "EN_OPERACION"

            elif estado == "EN_OPERACION":
                # Comprobación de salidas
                if tipo == "LONG":
                    if vela_15m['Minimo'] <= sl:
                        precio_salida = sl
                        res = "🔴 SL"
                        ratio_r = -1
                        comision_r = ((precio_entrada * 0.0002) + (precio_salida * 0.0002)) / riesgo
                        resultados.append({'Fecha_Setup': fecha_setup, 'Tipo': tipo, 'Entrada': round(precio_entrada,2), 'Resultado': res, 'Comision_R': round(comision_r, 3), 'R': ratio_r})
                        fecha_libre = vela_15m['Fecha']
                        break
                    elif vela_15m['Maximo'] >= tp:
                        precio_salida = tp
                        ratio_real = (tp - precio_entrada) / riesgo
                        res = f"🟢 TP (+{ratio_real:.1f}R)"
                        comision_r = ((precio_entrada * 0.0002) + (precio_salida * 0.0002)) / riesgo
                        resultados.append({'Fecha_Setup': fecha_setup, 'Tipo': tipo, 'Entrada': round(precio_entrada,2), 'Resultado': res, 'Comision_R': round(comision_r, 3), 'R': ratio_real})
                        fecha_libre = vela_15m['Fecha']
                        break
                else:  # SHORT
                    if vela_15m['Maximo'] >= sl:
                        precio_salida = sl
                        res = "🔴 SL"
                        ratio_r = -1
                        comision_r = ((precio_entrada * 0.0002) + (precio_salida * 0.0002)) / riesgo
                        resultados.append({'Fecha_Setup': fecha_setup, 'Tipo': tipo, 'Entrada': round(precio_entrada,2), 'Resultado': res, 'Comision_R': round(comision_r, 3), 'R': ratio_r})
                        fecha_libre = vela_15m['Fecha']
                        break
                    elif vela_15m['Minimo'] <= tp:
                        precio_salida = tp
                        ratio_real = (precio_entrada - tp) / riesgo
                        res = f"🟢 TP (+{ratio_real:.1f}R)"
                        comision_r = ((precio_entrada * 0.0002) + (precio_salida * 0.0002)) / riesgo
                        resultados.append({'Fecha_Setup': fecha_setup, 'Tipo': tipo, 'Entrada': round(precio_entrada,2), 'Resultado': res, 'Comision_R': round(comision_r, 3), 'R': ratio_real})
                        fecha_libre = vela_15m['Fecha']
                        break

            # Timeout: 24 horas
            if (vela_15m['Fecha'] - fecha_setup).total_seconds() > 86400:
                break

    return pd.DataFrame(resultados)


if __name__ == "__main__":
    run()
