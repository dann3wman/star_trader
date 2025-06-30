import random


from economy.agent import Agent, dump_agent
from economy import goods, jobs
from economy.market.book import OrderBook
from economy.market.history import SQLiteHistory, MarketHistory


class Market(object):
    _agents = None
    _book = None
    _history = None
    _lifespans = None

    def __init__(self, num_agents=15, history=None, job_counts=None,
                 initial_inv=10, initial_money=100):
        """Create a new market instance.

        Parameters
        ----------
        num_agents : int
            Total number of agents to create if ``job_counts`` is not
            provided.
        history : MarketHistory, optional
            History backend to use. Defaults to ``SQLiteHistory`` which
            persists trades to a SQLite database.
        job_counts : dict, optional
            Mapping of job names to the number of agents for that job. When
            supplied ``num_agents`` is ignored and agents are created exactly
            according to this mapping.
        initial_inv : int
            Starting inventory quantity for each agent.
        initial_money : int
            Starting money for each agent.
        """

        self._agents = []
        self._book = OrderBook()
        # Store trade history in SQLite by default
        self._history = history if history is not None else SQLiteHistory()
        self._lifespans = []

        job_list = list(jobs.all())
        if not job_list:
            return

        if job_counts:
            for job_name, count in job_counts.items():
                try:
                    recipe = jobs.by_name(job_name)
                except KeyError:
                    continue

                for _ in range(int(count)):
                    self._agents.append(
                        Agent(recipe, self, initial_inv=initial_inv,
                              initial_money=initial_money)
                    )

            # if no valid agents were added, fall back to uniform distribution
            if not self._agents:
                job_counts = None

        if not job_counts:
            agents_per_job = num_agents // len(job_list)
            leftover = num_agents % len(job_list)

            for recipe in job_list:
                for _ in range(agents_per_job):
                    self._agents.append(
                        Agent(recipe, self, initial_inv=initial_inv,
                              initial_money=initial_money)
                    )

            for recipe in job_list[:leftover]:
                self._agents.append(
                    Agent(recipe, self, initial_inv=initial_inv,
                          initial_money=initial_money)
                )

    def simulate(self, steps=1):
        # DEBUG
        for agent in self._agents:
            dump_agent(agent)

        for day in range(steps):
            self._history.open_day()
            self._book.clear_books()

            for agent in self._agents:
                self._book.add_orders(agent.make_offers())
                agent.do_production()

            daily_sd = {}
            for good in goods.all():
                trades = self._book.resolve_orders(good)
                self._history.add_trades(good, trades)
                daily_sd[good] = trades

            self._history.close_day()

            for agent in self._agents:
                agent.advance_day()

            dead_agents = [agent for agent in self._agents if agent.is_bankrupt]
            for agent in dead_agents:
                self._lifespans.append(agent.age)

            agents = [agent for agent in self._agents if not agent.is_bankrupt]

            while len(agents) < len(self._agents):
                job_weights = {}

                for good, trade in daily_sd.items():
                    delta = trade.supply - trade.demand
                    if delta > 0:
                        # Oversupply: favour consumers of this good
                        for job in jobs.all():
                            if any(step.good == good for step in job.inputs):
                                job_weights[job] = job_weights.get(job, 0) + delta
                    elif delta < 0:
                        # Excess demand: favour producers
                        for job in jobs.all():
                            if any(step.good == good for step in job.outputs):
                                job_weights[job] = job_weights.get(job, 0) + (-delta)

                if job_weights:
                    choices = list(job_weights.keys())
                    weights = list(job_weights.values())
                    recipe = random.choices(choices, weights=weights, k=1)[0]
                else:
                    recipe = random.choice(list(jobs.all()))

                agents.append(Agent(recipe, self))

            self._agents = agents

        # DEBUG
        for agent in self._agents:
            dump_agent(agent)

    def make_charts(self):
        # TODO: Decide if these will be general dependencies, or if charts will
        #       be an optional feature and thus these optional dependencies.
        import matplotlib.pyplot as plt
        import numpy as np

        hist = self.history()

        for good in goods.all():
            prices = []
            errs = [[], []]
            volumes = []

            days = list(range(1, len(hist[good]) + 1))

            for trades in hist[good]:
                if trades.mean is not None:
                    prices.append(trades.mean)

                    errs[0].append(trades.mean - trades.low)
                    errs[1].append(trades.high - trades.mean)
                else:
                    prices.append(np.nan)

                    errs[0].append(np.nan)
                    errs[1].append(np.nan)

                volumes.append(trades.volume or 0)

            plt.figure()

            plt.suptitle('{}-Day History for {}'.format(days[-1], good))

            ax1 = plt.subplot(211)
            ax1.set_ylabel('Price')
            ax1.set_xlabel('Day')
            ax1.errorbar(days, prices, yerr=errs)

            ax2 = plt.subplot(212, sharex=ax1)
            ax2.set_ylabel('Volume')
            ax2.bar(days, volumes)

            plt.subplots_adjust(wspace=0, hspace=0)

            plt.savefig('{}.png'.format(good), bbox_inches='tight')
            plt.close()

    def history(self, depth=None):
        return self._history.history(depth)

    def aggregate(self, good, depth=None):
        return self._history.aggregate(good, depth)

    def agent_stats(self):
        stats = []
        for agent in self._agents:
            stats.append({
                'name': agent.name,
                'job': agent.job,
                'money': agent.money,
                'profit': agent.total_profit,
                'trades': agent.trade_stats,
                'trade_totals': agent.trade_totals,
                'age': agent.age,
            })
        return stats

    def overview_stats(self):
        """Return high level market statistics."""
        avg_age = 0
        if self._agents:
            avg_age = sum(a.age for a in self._agents) / len(self._agents)
        avg_life = 0
        if self._lifespans:
            avg_life = sum(self._lifespans) / len(self._lifespans)
        return {
            'days_elapsed': self._history.day_number,
            'active_agents': len(self._agents),
            'average_age': avg_age,
            'average_lifespan': avg_life,
        }
