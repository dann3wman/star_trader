import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from economy.market.market import Market
from economy.market.history import SQLiteHistory
from economy.market.book import OrderBook
from economy.offer import Ask
from economy.exceptions import InvalidOrderTypeError


class TestMarketSimulation(unittest.TestCase):
    def test_simulation_does_not_run_out_of_agents(self):
        market = Market(num_agents=4)
        market.simulate(5)
        self.assertEqual(len(market.agent_stats()), 4)

    def test_daily_tax_causes_bankruptcy(self):
        market = Market(
            num_agents=1,
            job_counts={"Glass Maker": 1},
            initial_inv=0,
            initial_money=2,
            daily_tax=1,
        )
        market.simulate(2)
        stats = market.overview_stats()
        self.assertGreater(stats["average_lifespan"], 0)

    def test_trade_logging(self):
        history = SQLiteHistory(db_path=":memory:")
        market = Market(num_agents=3, history=history)
        market.simulate(1)
        with history._lock:
            cur = history._conn.execute("SELECT day FROM trade_log ORDER BY id LIMIT 1")
            first_day = cur.fetchone()[0]
            cur = history._conn.execute("SELECT COUNT(*) FROM trade_log")
            count = cur.fetchone()[0]
        self.assertGreater(count, 0)
        self.assertEqual(first_day, 1)

    def test_invalid_order_type_raises(self):
        book = OrderBook()

        class FakeOrder:
            good = None

        with self.assertRaises(InvalidOrderTypeError):
            book.add_order(FakeOrder())


if __name__ == "__main__":
    unittest.main()
