import ccxt
import pandas as pd
import os
import time

def descargar_historico(simbolo='BTC/USDT', temporalidad='1d', limite_velas=1000):
    exchange = ccxt.binance()
    print(f"Descargando {limite_velas} velas de {temporalidad}...")
    
    ahora = exchange.milliseconds()
    multiplicador = {'1d': 24*60*60, '1h': 60*60, '15m': 15*60}
    timestamp_inicio = ahora - (limite_velas * multiplicador[temporalidad] * 1000) 
    
    datos_crudos = []
    
    while len(datos_crudos) < limite_velas:
        try:
            # Pedimos bloques de 1000 en 1000
            bloque = exchange.fetch_ohlcv(simbolo, temporalidad, since=timestamp_inicio, limit=1000)
            if not bloque: break
            timestamp_inicio = bloque[-1][0] + 1
            datos_crudos.extend(bloque)
            time.sleep(0.2) # Pausa para no cabrear a Binance
        except Exception as e:
            print(f"Error en la descarga: {e}")
            break

    datos_crudos = datos_crudos[-limite_velas:]
    df = pd.DataFrame(datos_crudos, columns=['Fecha', 'Apertura', 'Maximo', 'Minimo', 'Cierre', 'Volumen'])
    df['Fecha'] = pd.to_datetime(df['Fecha'], unit='ms')
    return df

if __name__ == "__main__":
    os.makedirs('data', exist_ok=True)
    
    dias_historial = 180 # 6 MESES EXACTOS
    
    # 1. Macro (1D): 180 velas
    df_1d = descargar_historico(temporalidad='1d', limite_velas=dias_historial)
    df_1d.to_csv('data/btc_1d.csv', index=False)
    
    # 2. Setup (1H): 180 días * 24 horas = 4.320 velas
    df_1h = descargar_historico(temporalidad='1h', limite_velas=dias_historial * 24)
    df_1h.to_csv('data/btc_1h.csv', index=False)
    
    # 3. Gatillo (15m): 180 días * 24h * 4 cuartos = 17.280 velas
    df_15m = descargar_historico(temporalidad='15m', limite_velas=dias_historial * 24 * 4)
    df_15m.to_csv('data/btc_15m.csv', index=False)
    
    print("\n¡Base de datos Sincronizada (6 Meses) lista para operar!")