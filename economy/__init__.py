from .agent import Agent
from .inventory import Inventory
try:
    from .market.history import SQLiteHistory
except Exception:  # pragma: no cover - optional dependency
    SQLiteHistory = None
    __all__ = ['Agent', 'Inventory']
else:
    __all__ = ['Agent', 'Inventory', 'SQLiteHistory']

# try:
from .market import Market
from .db import rebuild_database
# except Exception:
#     # Importing Market pulls in optional dependencies such as PyYAML
#     # which may not be installed in minimal test environments. To keep
#     # imports lightweight and allow test discovery without these extras,
#     # ignore any errors when loading Market.
#     Market = None
# else:
__all__.append('Market')
__all__.append('rebuild_database')

