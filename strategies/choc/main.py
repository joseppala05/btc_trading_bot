"""CHoCH + macro strategy (current).

This file contains the complete backtest as it was before restructuring.
"""

import os
import sys

import pandas as pd

from backtest.motor_simulacion import simular_mtf
from indicators.macro import analyze_macro_1d
from indicators.setup_1h import analyze_setup_1h

# Ensure emojis and symbols print correctly in Windows PowerShell.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def run(assets=None, macro_window=5, zone_margin=0.05, risk_reward_ratio=2.0, sl_margin=0.01):
    assets = assets or ['btc', 'eth', 'sol', 'xrp', 'ada']
    all_results = []

    print("Starting Multi-Currency Backtest (Full Period)...")
    for asset in assets:
        print(f"\n[>] Analyzing {asset.upper()}...")

        # 1. Load tables
        df_1d = pd.read_csv(os.path.join('data', f'{asset}_1d.csv'), parse_dates=['Fecha'])
        df_1h = pd.read_csv(os.path.join('data', f'{asset}_1h.csv'), parse_dates=['Fecha'])
        df_15m = pd.read_csv(os.path.join('data', f'{asset}_15m.csv'), parse_dates=['Fecha'])

        # 2. Apply strategy
        df_1d = analyze_macro_1d(df_1d, window=macro_window)
        df_1h = analyze_setup_1h(df_1h, df_1d, zone_margin=zone_margin)

        # 3. Simulate
        df_results = simular_mtf(
            df_1h,
            df_15m,
            ratio_riesgo_beneficio=risk_reward_ratio,
            margen_sl=sl_margin,
        )

        if not df_results.empty:
            # Add a column to know which currency each trade is from
            df_results.insert(0, 'Asset', asset.upper())
            all_results.append(df_results)

    # --- MERGE ALL RESULTS ---
    if all_results:
        final_report = pd.concat(all_results, ignore_index=True)
        final_report = final_report.sort_values(by='Fecha_Setup')

        print("\n\n============================================================")
        print("      GLOBAL EXECUTED PORTFOLIO (BTC + ETH + SOL + XRP + ADA) ")
        print("============================================================")
        print(final_report.to_string(index=False))

        total = len(final_report)
        wins_full = len(final_report[final_report['Resultado'] == "🟢 TP FULL (+2R)"])
        wins_partial = len(final_report[final_report['Resultado'] == "🔵 TP_PARCIAL (+0.5R)"])
        losses = len(final_report[final_report['Resultado'] == "🔴 SL"])
        breakevens = len(final_report[final_report['Resultado'] == "⚪ BREAKEVEN"])

        total_wins = wins_full + wins_partial
        valid_operations = total - breakevens
        win_rate = (total_wins / valid_operations) * 100 if valid_operations > 0 else 0

        # Final Financial Calculations
        gross_profit_r = (wins_full * 2.0) + (wins_partial * 0.5) - losses
        total_commissions_r = final_report['Comision_R'].sum()
        net_profit_r = gross_profit_r - total_commissions_r

        print(f"\n--- TOTAL PORTFOLIO STATISTICS (2024-2026) ---")
        print(f"Total Global Operations: {total}")
        print(f"Total Wins (+2R): {wins_full}")
        print(f"Partial Wins (+0.5R): {wins_partial}")
        print(f"Losses (-1R): {losses}")
        print(f"Breakevens (0R): {breakevens}")
        print(f"Effective Win Rate: {win_rate:.2f}%")
        print(f"Total Commission Cost: -{total_commissions_r:.2f}R")
        print(f"\n>>> REAL NET PROFIT (After Commissions): +{net_profit_r:.2f}R <<<")
    else:
        print("\nNo operations were completed in the entire portfolio.")


if __name__ == "__main__":
    run()
