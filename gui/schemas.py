from flask_marshmallow import Marshmallow
from marshmallow import fields

ma = Marshmallow()

class AgentStatsSchema(ma.Schema):
    name = fields.String()
    job = fields.String()
    money = fields.Integer()
    profit = fields.Float()
    trades = fields.Dict(
        keys=fields.String(),
        values=fields.Dict(keys=fields.String(), values=fields.Integer()),
    )
    trade_totals = fields.Dict(keys=fields.String(), values=fields.Integer())
    age = fields.Integer()


class ResultEntrySchema(ma.Schema):
    low = fields.Float(allow_none=True)
    high = fields.Float(allow_none=True)
    current = fields.Float(allow_none=True)
    ratio = fields.Float(allow_none=True)
    prices = fields.List(fields.Float(allow_none=True))
    volumes = fields.List(fields.Integer(allow_none=True))


class SimulationResultSchema(ma.Schema):
    days = fields.Integer()
    results = fields.Dict(keys=fields.String(), values=fields.Nested(ResultEntrySchema))
    agents = fields.List(fields.Nested(AgentStatsSchema))


class OverviewSchema(ma.Schema):
    days_elapsed = fields.Integer()
    active_agents = fields.Integer()
    average_age = fields.Float()
    average_lifespan = fields.Float()


class AgentDetailSchema(ma.Schema):
    name = fields.String()
    job = fields.String()
    money = fields.Integer()
    total_profit = fields.Float()
    age = fields.Integer()
    inventory = fields.Dict(keys=fields.String(), values=fields.Integer())
    trades = fields.Dict(keys=fields.String(), values=fields.Integer())
