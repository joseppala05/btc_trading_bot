"""Strategy based on Fair Value Gaps (FVG).

Detects FVG in 1H timeframe and enters reversals when price touches the FVG border in 15M.
"""

import os
import sys

import pandas as pd

from backtest.motor_simulacion import simular_mtf
from indicators.fvg import identify_fvg

# Ensure emojis and symbols print correctly in Windows PowerShell.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def run(assets=None, risk_reward_ratio=2.0, sl_margin=0.01, min_gap_pct=0.01, confirmation_type='volume'):
    assets = assets or ['btc']
    all_results = []

    print("Starting FVG Multi-Currency Backtest...")
    for asset in assets:
        print(f"\n[>] Analyzing {asset.upper()}...")

        # 1. Load tables
        df_1h = pd.read_csv(os.path.join('data', f'{asset}_1h.csv'), parse_dates=['Fecha'])
        df_15m = pd.read_csv(os.path.join('data', f'{asset}_15m.csv'), parse_dates=['Fecha'])

        # 2. Identify FVG in 1H
        fvgs = identify_fvg(df_1h, min_gap_pct=min_gap_pct, confirmation_type=confirmation_type)
        print(f"   -> FVG detected: {len(fvgs)}")

        # 3. Simulate entries in 15M based on FVG
        df_results = simular_fvg(df_1h, df_15m, fvgs, risk_reward_ratio, sl_margin)

        if not df_results.empty:
            df_results.insert(0, 'Asset', asset.upper())
            all_results.append(df_results)

    # --- MERGE ALL RESULTS ---
    if all_results:
        final_report = pd.concat(all_results, ignore_index=True)
        final_report = final_report.sort_values(by='Fecha_Setup')

        print("\n\n============================================================")
        print("      GLOBAL FVG PORTFOLIO (BTC + ETH + SOL + XRP + ADA) ")
        print("============================================================")
        print(final_report.to_string(index=False))

        total = len(final_report)
        wins = len(final_report[final_report['Resultado'].str.startswith("🟢 TP")])
        losses = len(final_report[final_report['Resultado'] == "🔴 SL"])

        total_wins = wins
        valid_operations = total
        win_rate = (total_wins / valid_operations) * 100 if valid_operations > 0 else 0

        gross_profit_r = final_report['R'].sum()
        total_commissions_r = final_report['Comision_R'].sum()
        net_profit_r = gross_profit_r - total_commissions_r

        print(f"\n--- TOTAL PORTFOLIO STATISTICS (2024-2026) ---")
        print(f"Total Global Operations: {total}")
        print(f"Total Wins: {total_wins}")
        print(f"Losses (-1R): {losses}")
        print(f"Effective Win Rate: {win_rate:.2f}%")
        print(f"Total Commission Cost: -{total_commissions_r:.2f}R")
        print(f"\n>>> REAL NET PROFIT (After Commissions): {net_profit_r:+.2f}R <<<")
    else:
        print("\nNo operations were completed in the entire portfolio.")


def simulate_fvg(df_1h, df_15m, fvgs, risk_reward_ratio=2.0, sl_margin=0.01):
    """
    Simulates entries based on detected FVG in 1H, waiting for touches in 15M.
    """
    results = []
    free_date = pd.Timestamp('1970-01-01')

    for _, fvg in fvgs.iterrows():
        if fvg['Fecha'] <= free_date:
            continue

        trade_type = "LONG" if fvg['tipo'] == 'Bullish' else "SHORT"
        setup_date = fvg['Fecha']
        fvg_top = fvg['FVG_Top']
        fvg_bottom = fvg['FVG_Bottom']

        # Entry zone: FVG border
        entry_zone = fvg_bottom if trade_type == "LONG" else fvg_top

        # TP on the other side of the FVG
        fvg_tp = fvg_top if trade_type == "LONG" else fvg_bottom

        future_15m_candles = df_15m[df_15m['Fecha'] > setup_date]
        state = "WAITING_FOR_TOUCH"
        entry_price = sl = tp = risk = 0

        for i_15m, candle_15m in future_15m_candles.iterrows():
            if state == "WAITING_FOR_TOUCH":
                # Enter if touches the zone (for LONG: price drops to zone, for SHORT: rises to zone)
                if trade_type == "LONG" and candle_15m['Minimo'] <= entry_zone:
                    entry_price = entry_zone
                    sl = entry_price * (1 - sl_margin)
                    risk = entry_price - sl
                    if risk <= 0: break
                    tp = fvg_tp
                    state = "IN_OPERATION"
                elif trade_type == "SHORT" and candle_15m['Maximo'] >= entry_zone:
                    entry_price = entry_zone
                    sl = entry_price * (1 + sl_margin)
                    risk = sl - entry_price
                    if risk <= 0: break
                    tp = fvg_tp
                    state = "IN_OPERATION"

            elif state == "IN_OPERATION":
                # Check exits
                if trade_type == "LONG":
                    if candle_15m['Minimo'] <= sl:
                        exit_price = sl
                        res = "🔴 SL"
                        ratio_r = -1
                        commission_r = ((entry_price * 0.0002) + (exit_price * 0.0002)) / risk
                        results.append({'Fecha_Setup': setup_date, 'Tipo': trade_type, 'Entrada': round(entry_price,2), 'Resultado': res, 'Comision_R': round(commission_r, 3), 'R': ratio_r})
                        free_date = candle_15m['Fecha']
                        break
                    elif candle_15m['Maximo'] >= tp:
                        exit_price = tp
                        ratio_real = (tp - entry_price) / risk
                        res = f"🟢 TP (+{ratio_real:.1f}R)"
                        commission_r = ((entry_price * 0.0002) + (exit_price * 0.0002)) / risk
                        results.append({'Fecha_Setup': setup_date, 'Tipo': trade_type, 'Entrada': round(entry_price,2), 'Resultado': res, 'Comision_R': round(commission_r, 3), 'R': ratio_real})
                        free_date = candle_15m['Fecha']
                        break
                else:  # SHORT
                    if candle_15m['Maximo'] >= sl:
                        exit_price = sl
                        res = "🔴 SL"
                        ratio_r = -1
                        commission_r = ((entry_price * 0.0002) + (exit_price * 0.0002)) / risk
                        results.append({'Fecha_Setup': setup_date, 'Tipo': trade_type, 'Entrada': round(entry_price,2), 'Resultado': res, 'Comision_R': round(commission_r, 3), 'R': ratio_r})
                        free_date = candle_15m['Fecha']
                        break
                    elif candle_15m['Minimo'] <= tp:
                        exit_price = tp
                        ratio_real = (entry_price - tp) / risk
                        res = f"🟢 TP (+{ratio_real:.1f}R)"
                        commission_r = ((entry_price * 0.0002) + (exit_price * 0.0002)) / risk
                        results.append({'Fecha_Setup': setup_date, 'Tipo': trade_type, 'Entrada': round(entry_price,2), 'Resultado': res, 'Comision_R': round(commission_r, 3), 'R': ratio_real})
                        free_date = candle_15m['Fecha']
                        break

            # Timeout: 24 hours
            if (candle_15m['Fecha'] - setup_date).total_seconds() > 86400:
                break

    return pd.DataFrame(results)


if __name__ == "__main__":
    run()
