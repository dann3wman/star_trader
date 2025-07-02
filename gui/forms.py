from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange

from config import INITIAL_MONEY, INITIAL_INVENTORY


class BaseSimulationForm(FlaskForm):
    """Base fields for running a simulation."""

    num_agents = IntegerField(
        "Number of Agents",
        default=9,
        validators=[DataRequired(), NumberRange(min=1)],
    )
    days = IntegerField(
        "Days",
        default=5,
        validators=[DataRequired(), NumberRange(min=1)],
    )
    initial_money = IntegerField(
        "Initial Money",
        default=INITIAL_MONEY,
        validators=[NumberRange(min=0)],
    )
    initial_inv = IntegerField(
        "Initial Inventory",
        default=INITIAL_INVENTORY,
        validators=[NumberRange(min=0)],
    )
    submit = SubmitField("Run")

    class Meta:
        csrf = False


def SimulationForm(job_list):
    """Factory returning a form class with extra job fields."""

    class _SimulationForm(BaseSimulationForm):
        pass

    for job in job_list:
        slug = job.replace(" ", "_")
        setattr(
            _SimulationForm,
            f"job_{slug}",
            IntegerField(job, default=0, validators=[NumberRange(min=0)]),
        )
    return _SimulationForm
