import yfinance as yf
import pandas as pd
import os

def descargar_stock(ticker, temporalidad, periodo):
    print(f"Descargando {ticker} en {temporalidad} (Periodo: {periodo})...")
    
    # Descarga de datos
    df = yf.download(ticker, interval=temporalidad, period=periodo, progress=False)    

    if df.empty:
        print(f"[!] No se encontraron datos para {ticker} en {temporalidad}.")
        return df

    # Corrección para versiones nuevas de yfinance: aplanar columnas si vienen con niveles extra
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Limpiar y formatear para que sea idéntico al de Binance (CCXT)
    df = df.reset_index()
    
    # yfinance devuelve 'Date' para 1d y 'Datetime' para intradía (1h, 15m)
    columna_fecha = 'Datetime' if 'Datetime' in df.columns else 'Date'
    
    # Renombrar columnas para unificar con el motor de backtest
    df = df.rename(columns={
        columna_fecha: 'Fecha',
        'Open': 'Apertura',
        'High': 'Maximo',
        'Low': 'Minimo',
        'Close': 'Cierre',
        'Volume': 'Volumen'
    })
    
    # Seleccionar solo las columnas necesarias
    columnas = ['Fecha', 'Apertura', 'Maximo', 'Minimo', 'Cierre', 'Volumen']
    df = df[columnas].copy()

    # Limpieza de datos: Asegurar que los precios sean floats (números reales)
    for col in ['Apertura', 'Maximo', 'Minimo', 'Cierre']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Quitar zonas horarias para evitar errores de comparación con los datos de Binance
    df['Fecha'] = pd.to_datetime(df['Fecha']).dt.tz_localize(None)
    
    # Eliminar posibles filas vacías tras la conversión
    return df.dropna()

if __name__ == "__main__":
    os.makedirs('data', exist_ok=True)
    
    # Lista de los 5 stocks famosos
    stocks = ['AAPL', 'TSLA', 'MSFT', 'AMZN', 'NVDA']
    
    # Configuración de temporalidades (límites de Yahoo Finance)
    config_descarga = [
        ('1d', '2y'),   # 1 Día: 2 años
        ('1h', '730d'), # 1 Hora: ~2 años
        ('15m', '60d')  # 15 Min: Máximo 60 días
    ]
    
    for ticker in stocks:
        nombre_archivo = ticker.lower()
        print(f"\n======================================")
        print(f"=== DESCARGANDO DATOS PARA {ticker} ===")
        print(f"======================================")
        
        for temporalidad, periodo in config_descarga:
            df_stock = descargar_stock(ticker, temporalidad, periodo)
            
            if not df_stock.empty:
                ruta_guardado = f'data/{nombre_archivo}_{temporalidad}.csv'
                df_stock.to_csv(ruta_guardado, index=False)
                print(f"[OK] Guardado: {ruta_guardado} ({len(df_stock)} filas)")
                
    print("\n¡Base de datos de Stocks Sincronizada y lista!")