"""Trading boundary placeholder.

Order submission is deliberately absent during Phase 1. Future execution code must
invoke deterministic risk and portfolio gates before any paper-order SDK call.
"""

from killjoy.alpaca.client import AlpacaPaperClient

__all__ = ["AlpacaPaperClient"]
