import ccxt
import pandas as pd
import os
import time

def descargar_historico(simbolo='BTC/USDT', temporalidad='1d', limite_velas=1000):
    exchange = ccxt.binance()
    print(f"Descargando {limite_velas} velas de {temporalidad} para {simbolo}...")
    
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
            time.sleep(0.3) # Pausa de seguridad para 1 año de datos
        except Exception as e:
            print(f"Error en la descarga: {e}")
            break

    # Recortar por si Binance devuelve un par extra
    datos_crudos = datos_crudos[-limite_velas:]
    df = pd.DataFrame(datos_crudos, columns=['Fecha', 'Apertura', 'Maximo', 'Minimo', 'Cierre', 'Volumen'])
    df['Fecha'] = pd.to_datetime(df['Fecha'], unit='ms')
    return df

if __name__ == "__main__":
    os.makedirs('data', exist_ok=True)
    dias_historial = 365*2 # 1 AÑO ENTERO (Nota: tu comentario dice 1 año pero la variable multiplica por 2)
    
    # Solo criptomonedas aquí, ya que Binance no tiene los stocks
    monedas = [ 'XRP/USDT', 'ADA/USDT'] # 'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'ADA/USDT'
    
    for simbolo in monedas:
        nombre = simbolo.split('/')[0].lower() # Extrae 'btc', 'eth', 'sol', 'xrp', 'ada'
        print(f"\n======================================")
        print(f"=== DESCARGANDO DATOS PARA {nombre.upper()} ===")
        print(f"======================================")
        
        # 1. Macro (1D)
        df_1d = descargar_historico(simbolo=simbolo, temporalidad='1d', limite_velas=dias_historial)
        df_1d.to_csv(f'data/{nombre}_1d.csv', index=False)
        
        # 2. Setup (1H)
        df_1h = descargar_historico(simbolo=simbolo, temporalidad='1h', limite_velas=dias_historial * 24)
        df_1h.to_csv(f'data/{nombre}_1h.csv', index=False)
        
        # 3. Gatillo (15m)
        df_15m = descargar_historico(simbolo=simbolo, temporalidad='15m', limite_velas=dias_historial * 24 * 4)
        df_15m.to_csv(f'data/{nombre}_15m.csv', index=False)
    
    criptos_descargadas = ", ".join([m.split('/')[0] for m in monedas])
    print(f"\n¡Base de datos Sincronizada ({criptos_descargadas}) lista para operar!")