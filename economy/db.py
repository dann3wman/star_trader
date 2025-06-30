import os
import sqlite3

# Reuse the same database file as the simulation history so that all
# persistent data lives together. Users can override the path via the
# STAR_TRADER_DB environment variable.
DB_PATH = os.environ.get("STAR_TRADER_DB", "sim.db")


def get_connection():
    """Return a connection to the shared SQLite database."""
    return sqlite3.connect(DB_PATH)
