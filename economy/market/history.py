from collections import namedtuple
from functools import lru_cache
import logging
import sqlite3
import threading


from economy import goods


logger = logging.getLogger(__name__)


Trades = namedtuple('Trades', ['volume', 'low', 'high', 'mean', 'supply', 'demand'])


class MarketHistory(object):
    def __init__(self, max_depth=30):
        self._max_depth = max_depth
        self._history = {}
        self._day = None
        self._day_number = 0

        for good in goods.all():
            self._history[good] = []

    def open_day(self):
        if self._day is not None:
            logger.warning('Opening new day before previous day was properly closed. Its trades have been lost. You must call close_day() to commit trades to the history.')

        self._day_number += 1
        self._day = {}
        for good in goods.all():
            self._day[good] = None

    def add_trades(self, good, trades):
        if self._day is None:
            logger.warning('Implicitly opening a new day to record this trade. You should call open_day() yourself.')
            self.open_day()

        self._day[good] = trades

    def close_day(self):
        for good in self._day.keys():
            self._history[good].append(self._day[good])

            # Be lazy about our garbage collection
            if len(self._history[good]) > 1.5 * self._max_depth:
                self._history[good] = self._history[good][-self._max_depth:]

        self._day = None

        # Clear our cached aggregate data
        self.aggregate.cache_clear()

    def history(self, depth=None):
        if self._day is not None:
            logger.warning('Day has been left open. It will not appear in the history.')

        if depth is None or depth > self._max_depth:
            depth = self._max_depth

        hist = {}
        for good in goods.all():
            hist[good] = self._history[good][-depth:]

        return hist

    @lru_cache(maxsize=64)
    def aggregate(self, good, depth=None):
        if self._day is not None:
            logger.warning('Day has been left open. It will not appear in the history.')

        if depth is None or depth > self._max_depth:
            depth = self._max_depth

        hist = self._history[good][-depth:]
        low = None
        high = None
        current = None

        for trades in hist:
            if trades.volume == 0:
                # No trades on this day, ignore it
                continue

            try:
                low = min(low, trades.low)
            except TypeError:
                low = trades.low

            try:
                high = max(high, trades.high)
            except TypeError:
                high = trades.high

            current = trades.mean

        try:
            ratio = (current-low)/(high-low)
        except TypeError:
            ratio = None
        except ZeroDivisionError:
            # Special case to handle high and low being the same
            ratio = 0.5

        return (low, high, current, ratio)

    @property
    def day_number(self):
        return self._day_number



class SQLiteHistory(MarketHistory):
    """Persist market history to a SQLite database."""

    def __init__(self, db_path="sim.db", max_depth=30):
        self._db_path = db_path
        # Allow usage across threads but guard with a lock
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._lock = threading.Lock()
        with self._lock:
            self._conn.execute(
                """CREATE TABLE IF NOT EXISTS trades(
                    day INTEGER,
                    good TEXT,
                    volume INTEGER,
                    low INTEGER,
                    high INTEGER,
                    mean INTEGER,
                    supply INTEGER,
                    demand INTEGER
                )"""
            )
            self._conn.commit()

        super().__init__(max_depth=max_depth)

        # Load any existing data
        with self._lock:
            cur = self._conn.execute("SELECT MAX(day) FROM trades")
            row = cur.fetchone()
        self._day_number = row[0] or 0

        for good in goods.all():
            self._history[good] = []
            with self._lock:
                cur = self._conn.execute(
                    "SELECT volume, low, high, mean, supply, demand FROM trades WHERE good=? ORDER BY day",
                    (str(good),),
                )
                for r in cur.fetchall():
                    self._history[good].append(Trades(*r))

    def close_day(self):
        super().close_day()
        day = self._day_number
        with self._lock:
            cur = self._conn.cursor()
            for good in goods.all():
                trades = self._history[good][-1]
                cur.execute(
                    "INSERT INTO trades(day, good, volume, low, high, mean, supply, demand) VALUES (?,?,?,?,?,?,?,?)",
                    (
                        day,
                        str(good),
                        trades.volume,
                        trades.low,
                        trades.high,
                        trades.mean,
                        trades.supply,
                        trades.demand,
                    ),
                )
            self._conn.commit()

    def reset(self):
        """Clear all data from the database and memory."""
        with self._lock:
            self._conn.execute("DELETE FROM trades")
            self._conn.commit()
        self._history = {good: [] for good in goods.all()}
        self._day_number = 0

