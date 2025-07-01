import random
import logging

from .beliefs import Beliefs
from .offer import Ask, Bid, MIN_PRICE
from .inventory import Inventory
from .names import FIRST_NAMES, LAST_NAMES
from config import (
    INVENTORY_SIZE as DEFAULT_INVENTORY_SIZE,
    INITIAL_INVENTORY,
    INITIAL_MONEY,
)

logger = logging.getLogger(__name__)


def dump_agent(agent):
    inv = ""
    for item in agent._inventory._items:
        inv += ",{item},{qty}".format(
            item=item,
            qty=agent._inventory.query_inventory(item),
        )

    logger.debug(
        "{agent},{job}{inv},{money}¤".format(
            agent=agent._name,
            job=agent.job,
            inv=inv,
            money=agent._money,
        )
    )


class Agent(object):
    INVENTORY_SIZE = DEFAULT_INVENTORY_SIZE
    _inventory = None
    _recipe = None
    _market = None
    _money = 0
    _money_last_round = 0
    _name = None
    _initial_money = 0
    _trade_stats = None
    _age = 0
    beliefs = None

    def __init__(
        self, recipe, market, initial_inv=INITIAL_INVENTORY, initial_money=INITIAL_MONEY
    ):
        self._recipe = recipe
        self._market = market
        self._money = initial_money
        self._money_last_round = initial_money
        self._initial_money = initial_money
        self._name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

        self._trade_stats = {}
        self._age = 0

        self.beliefs = Beliefs()

        # Initialize inventory
        self._inventory = Inventory(self.INVENTORY_SIZE)
        qty = round(
            initial_inv / (len(self._recipe.inputs) + len(self._recipe.outputs))
        )
        for step in list(self._recipe.inputs) + list(self._recipe.outputs):
            self._inventory.set_qty(step.good, qty)

        for tool in self._recipe.tools:
            # Start with all necessary tools
            self._inventory.set_qty(tool.tool, tool.qty)

    @property
    def job(self):
        return str(self._recipe)

    @property
    def name(self):
        return self._name

    @property
    def money(self):
        return self._money

    @property
    def age(self):
        return self._age

    @property
    def total_profit(self):
        return self._money - self._initial_money

    @property
    def profit(self):
        return self._money - self._money_last_round

    @property
    def is_bankrupt(self):
        # TODO: TEMPORARY hack to prevent "harvesters"/"consumers" going bankrupt
        if len(self._recipe.inputs + self._recipe.outputs) <= 1:
            return False

        return self._money <= 0

    def do_production(self):
        for run in self._recipe.runs:
            if not self._can_produce():
                return

            for step in self._recipe.inputs:
                # Deduct any required input
                self._inventory.remove_item(step.good, step.qty)

            for step in self._recipe.outputs:
                # Add any output
                self._inventory.add_item(step.good, step.qty)

            for tool in self._recipe.tools:
                # Check for tool breakage
                if random.random() < tool.break_chance:
                    self._inventory.remove_item(tool.tool, 1)

    def make_offers(self):
        # From an Agent's perspective, making offers is the start of a round
        self._money_last_round = self._money

        space = self._inventory.available_space()
        for step in self._recipe.inputs:
            # Input into our recipe, make a bid to buy
            # We deliberately do not account for qty we're selling because
            # we don't know how many we'll actually sell in this round
            # TODO: Need to adjust Bid qty to avoid overflowing inventory
            #       if an Agent requires multiple inputs
            bid_qty = self._determine_trade_quantity(
                step.good,
                space,
                buying=True,
            )

            if bid_qty > 0:
                yield Bid(
                    step.good, bid_qty, self.beliefs.choose_price(step.good), self
                )

        for step in self._recipe.outputs:
            # We produce these, sell 'em
            ask_qty = self._determine_trade_quantity(
                step.good,
                self._inventory.query_inventory(step.good),
            )

            if ask_qty > 0:
                yield Ask(
                    step.good, ask_qty, self.beliefs.choose_price(step.good), self
                )

        for tool in self._recipe.tools:
            # Check if we need to buy any tools
            have = self._inventory.query_inventory(tool.tool)
            if have < tool.qty:
                yield Bid(
                    tool.tool,
                    tool.qty - have,
                    self.beliefs.choose_price(tool.tool),
                    self,
                )

    def give_money(self, amt, other):
        self._money -= amt
        other._money += amt

    def pay_tax(self, amount):
        """Deduct a daily flat tax from the agent's money."""
        self._money -= amount

    def give_items(self, item, amt, other):
        self._inventory.remove_item(item, amt)
        other._inventory.add_item(item, amt)

    def record_purchase(self, good, qty):
        stats = self._trade_stats.setdefault(good, {"bought": 0, "sold": 0})
        stats["bought"] += qty

    def record_sale(self, good, qty):
        stats = self._trade_stats.setdefault(good, {"bought": 0, "sold": 0})
        stats["sold"] += qty

    @property
    def trade_stats(self):
        return self._trade_stats

    @property
    def trade_totals(self):
        """Return total units bought and sold across all goods."""
        bought = sum(v["bought"] for v in self._trade_stats.values())
        sold = sum(v["sold"] for v in self._trade_stats.values())
        return {"bought": bought, "sold": sold}

    def advance_day(self):
        """Increment the agent's age by one day."""
        self._age += 1

    def _determine_trade_quantity(self, good, base_qty, buying=False, default=0.75):
        if base_qty <= 0:
            return 0

        ratio = self._market.aggregate(good)[3]

        if ratio is None:
            ratio = 0.75
        elif buying:
            ratio = 1 - ratio

        qty = round(base_qty * ratio)

        # Trade at least 1
        return max(1, qty)

    def _can_produce(self):
        space = self._inventory.available_space()

        for step in self._recipe.inputs:
            # Ensure there's enough input
            if step.qty > self._inventory.query_inventory(step.good):
                return False

            # This will be consumed in production, freeing up space
            space += step.qty

        for step in self._recipe.outputs:
            # Ensure there's room for the output
            space -= step.qty
            if space < 0:
                return False

        for tool in self._recipe.tools:
            # Ensure we have our tools
            if tool.qty > self._inventory.query_inventory(tool.tool):
                return False

        return True

    def _get_cost(self, good):
        if good not in [x.good for x in self._recipe.outputs]:
            # This is not an output, so our cost is 0
            return 0

        cost = 0
        outputs = sum([x.qty for x in self._recipe.outputs])

        for step in self._recipe.inputs:
            cost += step.qty * self.beliefs.get_belief(step.good)[0]

        return round(cost / max(1, outputs))
