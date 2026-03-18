"""Main runner that allows executing different strategies from the same repository.

Usage:
  python main.py                # Runs the default strategy
  python main.py --strategy choc
"""

import argparse
import importlib
import pkgutil
import strategies


def list_strategies():
    return sorted([name for _, name, _ in pkgutil.iter_modules(strategies.__path__)])


def main():
    parser = argparse.ArgumentParser(description="Trading strategies backtest")
    parser.add_argument("--strategy", default="choc", help="Name of the strategy to execute")
    args = parser.parse_args()

    available_strategies = list_strategies()
    if args.strategy not in available_strategies:
        raise SystemExit(f"Unknown strategy: {args.strategy}. Options: {', '.join(available_strategies)}")

    module_path = f"strategies.{args.strategy}.main"
    strategy_module = importlib.import_module(module_path)

    if hasattr(strategy_module, "run"):
        strategy_module.run()
    else:
        raise SystemExit(f"The strategy '{args.strategy}' does not define a run() function")


if __name__ == "__main__":
    main()
