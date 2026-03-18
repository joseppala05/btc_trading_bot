"""Runner principal que permite ejecutar diferentes estrategias desde el mismo repositorio.

Uso:
  python main.py                # Ejecuta la estrategia por defecto
  python main.py --strategy choc
"""

import argparse
import importlib
import pkgutil
import strategies


def listar_estrategias():
    return sorted([name for _, name, _ in pkgutil.iter_modules(strategies.__path__)])


def main():
    parser = argparse.ArgumentParser(description="Backtest de estrategias de trading")
    parser.add_argument("--strategy", default="choc", help="Nombre de la estrategia a ejecutar")
    args = parser.parse_args()

    estrategias_disponibles = listar_estrategias()
    if args.strategy not in estrategias_disponibles:
        raise SystemExit(f"Estrategia desconocida: {args.strategy}. Opciones: {', '.join(estrategias_disponibles)}")

    module_path = f"strategies.{args.strategy}.main"
    strategy_module = importlib.import_module(module_path)

    if hasattr(strategy_module, "run"):
        strategy_module.run()
    else:
        raise SystemExit(f"La estrategia '{args.strategy}' no define una función run()")


if __name__ == "__main__":
    main()
