import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from economy.market.market import Market


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


if __name__ == "__main__":
    unittest.main()
