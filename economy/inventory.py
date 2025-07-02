from .exceptions import (
    InsufficientItemsError,
    InsufficientSpaceError,
    InventoryError,
)


class Inventory(object):
    """Simple fixed-capacity inventory for agents."""

    def __init__(self, capacity):
        self._capacity = capacity
        self._items = {}

    def query_inventory(self, item=None):
        if item is None:
            return sum(self._items.values())
        else:
            return self._items.get(item, 0)

    def available_space(self):
        return self._capacity - self.query_inventory()

    def add_item(self, item, qty=1):
        if self.query_inventory() + qty > self._capacity:
            raise InsufficientSpaceError(
                "Not enough room in inventory; have {inv_qty}, tried to add {qty}".format(
                    inv_qty=self.query_inventory(),
                    qty=qty,
                )
            )
        if self.query_inventory(item) + qty < 0:
            raise InsufficientItemsError("Not enough items in inventory")

        self._items[item] = self.query_inventory(item) + qty

    def remove_item(self, item, qty=1):
        # Simply "add" the negative quantity
        self.add_item(item, abs(qty) * -1)

    def set_qty(self, item, qty):
        old_qty = self.query_inventory(item)
        try:
            self._items[item] = 0
            self.add_item(item, qty)
        except InventoryError:
            self._items[item] = old_qty
            raise
