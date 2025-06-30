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

    def test_daily_tax_deducts_money(self):
        market = Market(num_agents=1, job_counts={'Sand Digger': 1},
                        initial_money=100, daily_tax=5)
        market.simulate(3)
        agent_money = market.agent_stats()[0]['money']
        self.assertEqual(agent_money, 85)

if __name__ == '__main__':
    unittest.main()
