import pandas as pd
import os
from indicators.pivotes import calcular_pivotes
from indicators.tendencia import calcular_tendencia_y_volumen
import numpy as np
from indicators.position import generar_position
from backtest.motor_simulacion import simular_operaciones

# 1. Cargar los datos que descargamos previamente
ruta_datos = os.path.join('data', 'btc_1h.csv')
print("Cargando datos locales...")
df = pd.read_csv(ruta_datos)

# 2. Aplicar el cálculo de Soportes y Resistencias (con ventana de 5 velas)
print("Calculando Soportes y Resistencias matemáticos...")
df = calcular_pivotes(df, ventana=5)
df = calcular_tendencia_y_volumen(df)
df = generar_position(df)

# Mostrar solo las velas donde la estrategia encontró una entrada (Señal 1 o -1)
velas_con_operacion = df[df['Senal'] != 0]
print(f"\nSe encontraron {len(velas_con_operacion)} posibles operaciones en este histórico.")
print(velas_con_operacion[['Fecha', 'Cierre', 'Senal', 'Resistencia_Activa', 'Soporte_Activo']])


# --- FASE DE SIMULACIÓN (BACKTEST) ---
print("\nSimulando resultados de las operaciones (Ratio 1:1.5)...")
df_resultados = simular_operaciones(df)

# Mostrar la tabla de resultados
print(df_resultados.to_string(index=False))

# Calcular el Win Rate (Tasa de acierto)
total_operaciones = len(df_resultados)
ganadas = len(df_resultados[df_resultados['Resultado'] == "🟢 GANANCIA (TP)"])
perdidas = len(df_resultados[df_resultados['Resultado'] == "🔴 PERDIDA (SL)"])

if total_operaciones > 0:
    win_rate = (ganadas / total_operaciones) * 100
    print(f"\n--- RESUMEN FINAL ---")
    print(f"Total Operaciones: {total_operaciones}")
    print(f"Ganadas: {ganadas} | Perdidas: {perdidas}")
    print(f"Tasa de Acierto (Win Rate): {win_rate:.2f}%")