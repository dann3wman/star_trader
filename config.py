import os

DB_PATH = os.environ.get("STAR_TRADER_DB", "sim.db")
INITIAL_INVENTORY = int(os.environ.get("STAR_TRADER_INITIAL_INV", "10"))
INITIAL_MONEY = int(os.environ.get("STAR_TRADER_INITIAL_MONEY", "100"))
INVENTORY_SIZE = int(os.environ.get("STAR_TRADER_INVENTORY_SIZE", "15"))
DAILY_TAX = int(os.environ.get("STAR_TRADER_DAILY_TAX", "1"))
