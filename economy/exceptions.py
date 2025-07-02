class StarTraderError(Exception):
    """Base exception for Star Trader application."""


class InventoryError(StarTraderError):
    """Base class for inventory related errors."""


class InsufficientSpaceError(InventoryError):
    """Raised when adding items exceeds inventory capacity."""


class InsufficientItemsError(InventoryError):
    """Raised when attempting to remove more items than available."""


class OrderError(StarTraderError):
    """Base class for order book errors."""


class InvalidOrderTypeError(OrderError):
    """Raised when an unknown order type is added to the order book."""
