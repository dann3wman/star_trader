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

if __name__ == '__main__':
    unittest.main()
