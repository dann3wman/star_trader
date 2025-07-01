import random


from economy.agent import Agent, dump_agent
from economy import goods, jobs

from config import INITIAL_INVENTORY, INITIAL_MONEY, DAILY_TAX
from economy.market.book import OrderBook
from economy.market.history import SQLiteHistory, MarketHistory


class Market(object):
    _agents = None
    _book = None
    _history = None
    _lifespans = None

    def __init__(
        self,
        num_agents=15,
        history=None,
        job_counts=None,
        initial_inv=INITIAL_INVENTORY,
        initial_money=INITIAL_MONEY,
        daily_tax=DAILY_TAX,
    ):
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
        daily_tax : int
            Flat amount of money deducted from each agent every day.
        """

        self._agents = []
        self._book = OrderBook()
        # Store trade history in SQLite by default
        self._history = history if history is not None else SQLiteHistory()
        self._lifespans = []
        self._daily_tax = daily_tax

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
                        Agent(
                            recipe,
                            self,
                            initial_inv=initial_inv,
                            initial_money=initial_money,
                        )
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
                        Agent(
                            recipe,
                            self,
                            initial_inv=initial_inv,
                            initial_money=initial_money,
                        )
                    )

            for recipe in job_list[:leftover]:
                self._agents.append(
                    Agent(
                        recipe,
                        self,
                        initial_inv=initial_inv,
                        initial_money=initial_money,
                    )
                )

    def simulate(self, steps=1):
        """Run the market simulation for ``steps`` days."""
        self._debug_agents()

        for _ in range(steps):
            self._run_day()

        self._debug_agents()

    def _debug_agents(self) -> None:
        """Output debug information for all agents."""
        for agent in self._agents:
            dump_agent(agent)

    # -- Simulation helpers -------------------------------------------------

    def _run_day(self) -> None:
        self._open_day()
        self._collect_orders()
        daily_sd = self._resolve_all_orders()
        self._history.close_day()
        self._process_end_of_day(daily_sd)

    def _open_day(self) -> None:
        self._history.open_day()
        self._book.clear_books()

    def _collect_orders(self) -> None:
        for agent in self._agents:
            self._book.add_orders(agent.make_offers())
            agent.do_production()

    def _resolve_all_orders(self):
        daily_sd = {}
        for good in goods.all():
            trades = self._book.resolve_orders(
                good,
                record_trade=self._history.record_trade,
                day=self._history.day_number,
            )
            self._history.add_trades(good, trades)
            daily_sd[good] = trades
        return daily_sd

    def _process_end_of_day(self, daily_sd) -> None:
        for agent in self._agents:
            agent.pay_tax(self._daily_tax)
            agent.advance_day()

        dead_agents = [agent for agent in self._agents if agent.is_bankrupt]
        for agent in dead_agents:
            self._lifespans.append(agent.age)

        agents = [agent for agent in self._agents if not agent.is_bankrupt]

        while len(agents) < len(self._agents):
            agents.append(self._spawn_agent(daily_sd))

        self._agents = agents

    def _spawn_agent(self, daily_sd):
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

        return Agent(recipe, self)

    def make_charts(self):
        """Generate interactive charts for price and volume using Plotly."""
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        hist = self.history()

        for good in goods.all():
            days = list(range(1, len(hist[good]) + 1))
            prices = []
            low_err = []
            high_err = []
            volumes = []

            for trades in hist[good]:
                prices.append(trades.mean)
                if trades.mean is not None:
                    low_err.append(trades.mean - trades.low)
                    high_err.append(trades.high - trades.mean)
                else:
                    low_err.append(None)
                    high_err.append(None)
                volumes.append(trades.volume or 0)

            fig = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.1,
                subplot_titles=(f"{good} Price", f"{good} Volume"),
            )

            fig.add_trace(
                go.Scatter(
                    x=days,
                    y=prices,
                    error_y=dict(array=high_err, arrayminus=low_err, type="data"),
                    mode="lines+markers",
                    name="Price",
                ),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Bar(x=days, y=volumes, name="Volume"),
                row=2,
                col=1,
            )

            fig.update_layout(
                height=500, width=700, title=f"{len(days)}-Day History for {good}"
            )
            fig.write_html(f"{good}.html", include_plotlyjs="cdn")

    def history(self, depth=None):
        return self._history.history(depth)

    def aggregate(self, good, depth=None):
        return self._history.aggregate(good, depth)

    def agent_stats(self):
        stats = []
        for agent in self._agents:
            stats.append(
                {
                    "name": agent.name,
                    "job": agent.job,
                    "money": agent.money,
                    "profit": agent.total_profit,
                    "trades": agent.trade_stats,
                    "trade_totals": agent.trade_totals,
                    "age": agent.age,
                }
            )
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
            "days_elapsed": self._history.day_number,
            "active_agents": len(self._agents),
            "average_age": avg_age,
            "average_lifespan": avg_life,
        }
