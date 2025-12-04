"""
Task 1: Pnml Parsing
- Re-exports Place, Transition, PNModel from model.py
- Provides a convenience function load_pnml(path) that later tasks can import.
"""

from model import Place, Transition, PNModel

def load_pnml(path: str) -> PNModel | None:
    """Convenience wrapper around PNModel.load_pnml()."""
    return PNModel.load_pnml(path)


__all__ = ["Place", "Transition", "PNModel", "load_pnml"]
