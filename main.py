import pandas as pd
import os
from indicators.macro import analizar_macro_1d
from indicators.setup_1h import analizar_setup_1h
from backtest.motor_simulacion import simular_mtf

# --- CARGAR TABLAS ---
print("Cargando base de datos Multi-Temporalidad...")
df_1d = pd.read_csv(os.path.join('data', 'btc_1d.csv'), parse_dates=['Fecha'])
df_1h = pd.read_csv(os.path.join('data', 'btc_1h.csv'), parse_dates=['Fecha'])
df_15m = pd.read_csv(os.path.join('data', 'btc_15m.csv'), parse_dates=['Fecha']) # CAMBIO A 15M

# --- APLICAR LÓGICA ---
print("Calculando Muros Macro (1D)...")
df_1d = analizar_macro_1d(df_1d, ventana=5)

print("Buscando Setups, Fibo y CHoCH (1H)...")
df_1h = analizar_setup_1h(df_1h, df_1d, margen_zona=0.015)

print("Simulando ejecuciones en 15 Minutos (Ratio 1:2)...")
df_resultados = simular_mtf(df_1h, df_15m, ratio_riesgo_beneficio=2.0) # CAMBIO A 15M

# --- RESULTADOS FINALES ---
if not df_resultados.empty:
    print("\n--- OPERACIONES EJECUTADAS (CON GATILLO 15M) ---")
    print(df_resultados.to_string(index=False))
    
    total = len(df_resultados)
    ganadas = len(df_resultados[df_resultados['Resultado'] == "🟢 TP"])
    win_rate = (ganadas / total) * 100
    
    print(f"\nTotal Operaciones: {total} | Ganadas: {ganadas} | Win Rate: {win_rate:.2f}%")
else:
    print("\nNo se completó ninguna operación. (El precio no hizo el pullback al Fibo o la MA no dio entrada).")