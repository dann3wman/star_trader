import random
import logging


from economy.market.history import Trades
from economy.offer import Ask, Bid

logger = logging.getLogger(__name__)


class OrderBook(object):
    def __init__(self):
        self.clear_books()

    def clear_books(self):
        self._asks = {}
        self._bids = {}

    def add_order(self, order):
        if isinstance(order, Ask):
            if order.good not in self._asks:
                self._asks[order.good] = []
            self._asks[order.good].append(order)
        elif isinstance(order, Bid):
            if order.good not in self._bids:
                self._bids[order.good] = []
            self._bids[order.good].append(order)
        else:
            raise ValueError("Order is not an Ask or a Bid")

    def add_orders(self, orders):
        for order in orders:
            self.add_order(order)

    def resolve_orders(self, good, record_trade=None, day=None):
        asks = self._asks.get(good, [])
        bids = self._bids.get(good, [])

        units_sold = 0
        total_value = 0

        low = None
        high = None

        supply = sum([ask.units for ask in asks])
        demand = sum([bid.units for bid in bids])

        # First shuffle the orders to ensure Agent ordering not a factor
        random.shuffle(asks)
        random.shuffle(bids)

        # Now sort by price
        asks.sort(key=lambda o: o.unit_price, reverse=True)
        bids.sort(key=lambda o: o.unit_price)

        while asks and bids:
            ask = asks.pop()
            bid = bids.pop()

            qty = min(ask.units, bid.units)
            price = round((ask.unit_price + bid.unit_price) / 2)

            try:
                low = min(low, price)
            except TypeError:
                low = price

            try:
                high = max(high, price)
            except TypeError:
                high = price

            units_sold += qty
            total_value += qty * price

            bid.agent.give_money(qty * price, ask.agent)
            ask.agent.give_items(good, qty, bid.agent)
            bid.agent.record_purchase(good, qty)
            ask.agent.record_sale(good, qty)

            if record_trade:
                if day is not None:
                    record_trade(day, bid.agent.name, ask.agent.name, good, qty, price)
                else:
                    record_trade(bid.agent.name, ask.agent.name, good, qty, price)

            bid.agent.beliefs.update(good, price)
            ask.agent.beliefs.update(good, price)

            logger.debug(
                "Bid: %s units of %s for %s; Ask: %s units of %s for %s; Cleared %s units for %s",
                bid.units,
                bid.good,
                bid.unit_price,
                ask.units,
                ask.good,
                ask.unit_price,
                qty,
                price,
            )

            ask.units -= qty
            bid.units -= qty

            if ask.units > 0:
                asks.append(ask)

            if bid.units > 0:
                bids.append(bid)

        if units_sold > 0:
            unit_price = round(total_value / units_sold)

            while asks:
                # Unsuccessful Asks
                ask = asks.pop()
                ask.agent.beliefs.update(good, unit_price, False)

            while bids:
                # Unsuccessful Bids
                bid = bids.pop()
                bid.agent.beliefs.update(good, unit_price, False)

            logger.info(
                "Sold %s %s at an average price of %s",
                units_sold,
                good,
                unit_price,
            )
        else:
            unit_price = None
            logger.info("0 units of %s were traded today", good)

        return Trades(
            low=low,
            high=high,
            volume=units_sold,
            mean=unit_price,
            supply=supply,
            demand=demand,
        )
