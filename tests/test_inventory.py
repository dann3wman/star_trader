import unittest

# Ensure the project root is on the Python path so that imports from the
# `economy` package succeed when tests are run directly or via pytest.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from economy.agent import Inventory


class TestInventory(unittest.TestCase):
    def test_add_items_up_to_capacity(self):
        inv = Inventory(capacity=3)
        inv.add_item('apple', 2)
        inv.add_item('banana', 1)
        self.assertEqual(inv.query_inventory(), 3)
        self.assertEqual(inv.available_space(), 0)
        self.assertEqual(inv.query_inventory('apple'), 2)
        self.assertEqual(inv.query_inventory('banana'), 1)

    def test_add_items_over_capacity_raises(self):
        inv = Inventory(capacity=2)
        inv.add_item('apple', 2)
        with self.assertRaises(ValueError):
            inv.add_item('banana', 1)

    def test_remove_items_updates_quantities(self):
        inv = Inventory(capacity=5)
        inv.add_item('apple', 3)
        inv.add_item('banana', 1)
        inv.remove_item('apple', 2)
        self.assertEqual(inv.query_inventory('apple'), 1)
        self.assertEqual(inv.available_space(), 3)
        inv.remove_item('banana', 1)
        self.assertEqual(inv.query_inventory('banana'), 0)
        self.assertEqual(inv.available_space(), 4)


if __name__ == '__main__':
    unittest.main()
