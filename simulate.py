import argparse
import logging

from economy.market.market import Market
from economy.market.history import SQLiteHistory

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Run or control the Star Trader simulation")
    parser.add_argument("--step", type=int, default=1, help="Number of days to simulate (default: 1)")
    parser.add_argument("--reset", action="store_true", help="Reset stored simulation data")
    parser.add_argument("--num-agents", type=int, default=9, help="Number of agents when starting a new simulation")
    parser.add_argument("--db", default="sim.db", help="SQLite database file")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    history = SQLiteHistory(db_path=args.db)

    if args.reset:
        history.reset()
        logger.info("Simulation reset.")
        return

    market = Market(num_agents=args.num_agents, history=history)
    market.simulate(args.step)
    logger.info("Simulated up to day %s.", history.day_number)


if __name__ == "__main__":
    main()
