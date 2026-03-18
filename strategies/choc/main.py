"""Estrategia CHoCH + macro (actual).

Este archivo contiene el backtest completo tal como estaba antes de la reestructuración.
"""

import os
import sys

import pandas as pd

from backtest.motor_simulacion import simular_mtf
from indicators.macro import analizar_macro_1d
from indicators.setup_1h import analizar_setup_1h

# Aseguramos que los emojis y símbolos se impriman bien en Windows PowerShell.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def run(activos=None, ventana_macro=5, margen_zona=0.05, ratio_riesgo_beneficio=2.0, margen_sl=0.01):
    activos = activos or ['btc', 'eth', 'sol', 'xrp', 'ada']
    todos_los_resultados = []

    print("Iniciando Backtest Multi-Moneda (Periodo Completo)...")
    for activo in activos:
        print(f"\n[>] Analizando {activo.upper()}...")

        # 1. Cargar tablas
        df_1d = pd.read_csv(os.path.join('data', f'{activo}_1d.csv'), parse_dates=['Fecha'])
        df_1h = pd.read_csv(os.path.join('data', f'{activo}_1h.csv'), parse_dates=['Fecha'])
        df_15m = pd.read_csv(os.path.join('data', f'{activo}_15m.csv'), parse_dates=['Fecha'])

        # 2. Aplicar estrategia
        df_1d = analizar_macro_1d(df_1d, ventana=ventana_macro)
        df_1h = analizar_setup_1h(df_1h, df_1d, margen_zona=margen_zona)

        # 3. Simular
        df_resultados = simular_mtf(
            df_1h,
            df_15m,
            ratio_riesgo_beneficio=ratio_riesgo_beneficio,
            margen_sl=margen_sl,
        )

        if not df_resultados.empty:
            # Añadimos una columna para saber de qué moneda es cada trade
            df_resultados.insert(0, 'Activo', activo.upper())
            todos_los_resultados.append(df_resultados)

    # --- UNIR TODOS LOS RESULTADOS ---
    if todos_los_resultados:
        reporte_final = pd.concat(todos_los_resultados, ignore_index=True)
        reporte_final = reporte_final.sort_values(by='Fecha_Setup')

        print("\n\n============================================================")
        print("      PORTAFOLIO GLOBAL EJECUTADO (BTC + ETH + SOL + XRP + ADA) ")
        print("============================================================")
        print(reporte_final.to_string(index=False))

        total = len(reporte_final)
        ganadas_full = len(reporte_final[reporte_final['Resultado'] == "🟢 TP FULL (+2R)"])
        ganadas_parciales = len(reporte_final[reporte_final['Resultado'] == "🔵 TP_PARCIAL (+0.5R)"])
        perdidas = len(reporte_final[reporte_final['Resultado'] == "🔴 SL"])
        empates = len(reporte_final[reporte_final['Resultado'] == "⚪ BREAKEVEN"])

        total_victorias = ganadas_full + ganadas_parciales
        operaciones_validas = total - empates
        win_rate = (total_victorias / operaciones_validas) * 100 if operaciones_validas > 0 else 0

        # Cálculos Financieros Finales
        ganancia_bruta_r = (ganadas_full * 2.0) + (ganadas_parciales * 0.5) - perdidas
        comisiones_totales_r = reporte_final['Comision_R'].sum()
        ganancia_neta_r = ganancia_bruta_r - comisiones_totales_r

        print(f"\n--- ESTADÍSTICAS DEL PORTAFOLIO TOTAL (2024-2026) ---")
        print(f"Total Operaciones Globales: {total}")
        print(f"Victorias Totales (+2R): {ganadas_full}")
        print(f"Victorias Parciales (+0.5R): {ganadas_parciales}")
        print(f"Perdidas (-1R): {perdidas}")
        print(f"Empates (0R): {empates}")
        print(f"Win Rate Efectivo: {win_rate:.2f}%")
        print(f"Coste Total en Comisiones: -{comisiones_totales_r:.2f}R")
        print(f"\n>>> BENEFICIO NETO REAL (Tras Comisiones): +{ganancia_neta_r:.2f}R <<<")
    else:
        print("\nNo se completó ninguna operación en todo el portafolio.")


if __name__ == "__main__":
    run()
