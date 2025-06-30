from collections import namedtuple
import random


from .beliefs import Beliefs
from .offer import Ask,Bid,MIN_PRICE


def dump_agent(agent):
    inv = ''
    for item in agent._inventory._items:
        inv += ',{item},{qty}'.format(
                item = item,
                qty = agent._inventory.query_inventory(item),
                )

    print('{agent},{job}{inv},{money}¤'.format(
        agent = agent._name,
        job = agent.job,
        inv = inv,
        money = agent._money,
        ))


class Inventory(object):
    _capacity = 0
    _items = None

    def __init__(self, capacity):
        self._capacity = capacity
        self._items = {}

    def query_inventory(self, item=None):
        if item is None:
            return sum(self._items.values())
        else:
            return self._items.get(item, 0)

    def available_space(self):
        return self._capacity - self.query_inventory()

    def add_item(self, item, qty=1):
        if self.query_inventory() + qty > self._capacity:
            raise ValueError("Not enough room in inventory; have {inv_qty}, tried to add {qty}".format(
                inv_qty = self.query_inventory(),
                qty = qty,
                ))
        if self.query_inventory(item) + qty < 0:
            raise ValueError("Not enough items in inventory")

        self._items[item] = self.query_inventory(item) + qty

    def remove_item(self, item, qty=1):
        # Simply "add" the negative quantity
        self.add_item(item, abs(qty) * -1)

    def set_qty(self, item, qty):
        old_qty = self.query_inventory(item)

        try:
            self._items[item] = 0
            self.add_item(item, qty)
        except:
            self._items[item] = old_qty
            raise


class Agent(object):
    INVENTORY_SIZE = 15
    _inventory = None
    _recipe = None
    _market = None
    _money = 0
    _money_last_round = 0
    _name = None
    _initial_money = 0
    _trade_stats = None
    beliefs = None

    def __init__(self, recipe, market, initial_inv=10, initial_money=100):
        self._recipe = recipe
        self._market = market
        self._money = initial_money
        self._money_last_round = initial_money
        self._initial_money = initial_money
        self._name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

        self._trade_stats = {}

        self.beliefs = Beliefs()

        # Initialize inventory
        self._inventory = Inventory(self.INVENTORY_SIZE)
        qty = round(initial_inv / (len(self._recipe.inputs)+len(self._recipe.outputs)))
        for good,*_ in self._recipe.inputs+self._recipe.outputs:
            self._inventory.set_qty(good, qty)

        for tool,qty,break_chance in self._recipe.tools:
            # Start with all necessary tools
            self._inventory.set_qty(tool,qty)

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
    def total_profit(self):
        return self._money - self._initial_money

    @property
    def profit(self):
        return self._money - self._money_last_round

    def apply_tax(self, amount):
        """Deduct a flat tax from the agent's money."""
        self._money -= amount

    @property
    def is_bankrupt(self):
        # TODO: TEMPORARY hack to prevent "harvesters"/"consumers" going bankrupt
        if len(self._recipe.inputs+self._recipe.outputs) <= 1:
            return False

        return self._money <= 0

    def do_production(self):
        for run in self._recipe.runs:
            if not self._can_produce():
                return

            for good,qty in self._recipe.inputs:
                # Deduct any required input
                self._inventory.remove_item(good, qty)

            for good,qty in self._recipe.outputs:
                # Add any output
                self._inventory.add_item(good, qty)

            for tool,qty,break_chance in self._recipe.tools:
                # Check for tool breakage
                if random.random() < break_chance:
                    self._inventory.remove_item(tool, 1)

    def make_offers(self):
        # From an Agent's perspective, making offers is the start of a round
        self._money_last_round = self._money

        space = self._inventory.available_space()
        for good,qty in self._recipe.inputs:
            # Input into our recipe, make a bid to buy
            # We deliberately do not account for qty we're selling because
            # we don't know how many we'll actually sell in this round
            # TODO: Need to adjust Bid qty to avoid overflowing inventory
            #       if an Agent requires multiple inputs
            bid_qty = self._determine_trade_quantity(
                good,
                space,
                buying=True,
            )

            if bid_qty > 0:
                yield Bid(good, bid_qty, self.beliefs.choose_price(good), self)

        for good,qty in self._recipe.outputs:
            # We produce these, sell 'em
            ask_qty = self._determine_trade_quantity(
                good,
                self._inventory.query_inventory(good),
            )

            if ask_qty > 0:
                yield Ask(good, ask_qty, self.beliefs.choose_price(good), self)

        for tool,qty,break_chance in self._recipe.tools:
            # Check if we need to buy any tools
            have = self._inventory.query_inventory(tool)
            if have < qty:
                yield Bid(tool, qty-have, self.beliefs.choose_price(tool), self)

    def give_money(self, amt, other):
        self._money -= amt
        other._money += amt

    def give_items(self, item, amt, other):
        self._inventory.remove_item(item, amt)
        other._inventory.add_item(item, amt)

    def record_purchase(self, good, qty):
        stats = self._trade_stats.setdefault(good, {'bought': 0, 'sold': 0})
        stats['bought'] += qty

    def record_sale(self, good, qty):
        stats = self._trade_stats.setdefault(good, {'bought': 0, 'sold': 0})
        stats['sold'] += qty

    @property
    def trade_stats(self):
        return self._trade_stats

    @property
    def trade_totals(self):
        """Return total units bought and sold across all goods."""
        bought = sum(v['bought'] for v in self._trade_stats.values())
        sold = sum(v['sold'] for v in self._trade_stats.values())
        return {'bought': bought, 'sold': sold}

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

        for good,qty in self._recipe.inputs:
            # Ensure there's enough input
            if qty > self._inventory.query_inventory(good):
                return False

            # This will be consumed in production, freeing up space
            space += qty

        for good,qty in self._recipe.outputs:
            # Ensure there's room for the output
            space -= qty
            if space < 0:
                return False

        for tool,qty,break_chance in self._recipe.tools:
            # Ensure we have our tools
            if qty > self._inventory.query_inventory(tool):
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

        return round(cost/max(1,outputs))

FIRST_NAMES = [
    'James',
    'Mary',
    'John',
    'Patricia',
    'Robert',
    'Jennifer',
    'Michael',
    'Elizabeth',
    'William',
    'Linda',
    'David',
    'Barbara',
    'Richard',
    'Susan',
    'Joseph',
    'Jessica',
    'Thomas',
    'Margaret',
    'Charles',
    'Sarah',
    'Christopher',
    'Karen',
    'Daniel',
    'Nancy',
    'Matthew',
    'Betty',
    'Anthony',
    'Lisa',
    'Donald',
    'Dorothy',
    'Mark',
    'Sandra',
    'Paul',
    'Ashley',
    'Steven',
    'Kimberly',
    'Andrew',
    'Donna',
    'Kenneth',
    'Carol',
    'George',
    'Michelle',
    'Joshua',
    'Emily',
    'Kevin',
    'Amanda',
    'Brian',
    'Helen',
    'Edward',
    'Melissa',
    'Ronald',
    'Deborah',
    'Timothy',
    'Stephanie',
    'Jason',
    'Laura',
    'Jeffrey',
    'Rebecca',
    'Ryan',
    'Sharon',
    'Gary',
    'Cynthia',
    'Jacob',
    'Kathleen',
    'Nicholas',
    'Amy',
    'Eric',
    'Shirley',
    'Stephen',
    'Anna',
    'Jonathan',
    'Angela',
    'Larry',
    'Ruth',
    'Justin',
    'Brenda',
    'Scott',
    'Pamela',
    'Frank',
    'Nicole',
    'Brandon',
    'Katherine',
    'Raymond',
    'Virginia',
    'Gregory',
    'Catherine',
    'Benjamin',
    'Christine',
    'Samuel',
    'Samantha',
    'Patrick',
    'Debra',
    'Alexander',
    'Janet',
    'Jack',
    'Rachel',
    'Dennis',
    'Carolyn',
    'Jerry',
    'Emma',
    'Tyler',
    'Maria',
    'Aaron',
    'Heather',
    'Henry',
    'Diane',
    'Douglas',
    'Julie',
    'Jose',
    'Joyce',
    'Peter',
    'Evelyn',
    'Adam',
    'Frances',
    'Zachary',
    'Joan',
    'Nathan',
    'Christina',
    'Walter',
    'Kelly',
    'Harold',
    'Victoria',
    'Kyle',
    'Lauren',
    'Carl',
    'Martha',
    'Arthur',
    'Judith',
    'Gerald',
    'Cheryl',
    'Roger',
    'Megan',
    'Keith',
    'Andrea',
    'Jeremy',
    'Ann',
    'Terry',
    'Alice',
    'Lawrence',
    'Jean',
    'Sean',
    'Doris',
    'Christian',
    'Jacqueline',
    'Albert',
    'Kathryn',
    'Joe',
    'Hannah',
    'Ethan',
    'Olivia',
    'Austin',
    'Gloria',
    'Jesse',
    'Marie',
    'Willie',
    'Teresa',
    'Billy',
    'Sara',
    'Bryan',
    'Janice',
    'Bruce',
    'Julia',
    'Jordan',
    'Grace',
    'Ralph',
    'Judy',
    'Roy',
    'Theresa',
    'Noah',
    'Rose',
    'Dylan',
    'Beverly',
    'Eugene',
    'Denise',
    'Wayne',
    'Marilyn',
    'Alan',
    'Amber',
    'Juan',
    'Madison',
    'Louis',
    'Danielle',
    'Russell',
    'Brittany',
    'Gabriel',
    'Diana',
    'Randy',
    'Abigail',
    'Philip',
    'Jane',
    'Harry',
    'Natalie',
    'Vincent',
    'Lori',
    'Bobby',
    'Tiffany',
    'Johnny',
    'Alexis',
    'Logan',
    'Kayla',
]

LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
    'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson',
    'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez',
    'Thompson', 'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis',
    'Robinson', 'Walker', 'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres',
    'Nguyen', 'Hill', 'Flores', 'Green', 'Adams', 'Nelson', 'Baker', 'Hall',
    'Rivera', 'Campbell', 'Mitchell', 'Carter', 'Roberts'
]

