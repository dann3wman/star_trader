import os
import sqlite3

# Reuse the same database file as the simulation history so that all
# persistent data lives together. Users can override the path via the
# STAR_TRADER_DB environment variable.
DB_PATH = os.environ.get("STAR_TRADER_DB", "sim.db")


def get_connection():
    """Return a connection to the shared SQLite database."""
    return sqlite3.connect(DB_PATH)


def rebuild_database():
    """Recreate goods and jobs tables from YAML files."""
    conn = get_connection()
    with conn:
        conn.execute("DROP TABLE IF EXISTS job_tools")
        conn.execute("DROP TABLE IF EXISTS job_outputs")
        conn.execute("DROP TABLE IF EXISTS job_inputs")
        conn.execute("DROP TABLE IF EXISTS jobs")
        conn.execute("DROP TABLE IF EXISTS goods")
    conn.close()

    # Clear any cached data and reload from YAML
    from . import goods as goods_mod, jobs as jobs_mod

    goods_mod._goods.clear()
    goods_mod._by_name.clear()
    jobs_mod._jobs.clear()
    jobs_mod._by_name.clear()

    goods_mod._load_goods()
    jobs_mod._load_jobs()

