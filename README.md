# Star Trader

Star Trader is a small experiment in modelling a trading economy. It contains a very
simple market engine, a set of autonomous agents and a few basic goods and job
recipes. Agents place bids and asks on the market, perform production based on
available goods and tools and adjust their beliefs about prices over time.

## Directory layout

```
.
├── data/      # YAML files describing goods and job recipes
└── economy/   # Python package implementing the simulation
    ├── agent.py       # Agent behaviour and inventory management
    ├── beliefs.py     # Price beliefs used by agents
    ├── goods.py       # Load goods from `data/goods.yml`
    ├── jobs.py        # Load jobs from `data/jobs.yml`
    ├── offer.py       # Ask/Bid definitions
    └── market/        # Market engine and order book
        ├── market.py  # `Market` class and simulation loop
        ├── book.py    # Order book matching bids and asks
        └── history.py # Tracking price history
```

### `data/`

The `data` folder contains YAML configuration files. `goods.yml` lists all tradeable
goods and their storage size while `jobs.yml` defines the jobs that agents can
perform, including the required inputs and produced outputs.

### `economy/`

The `economy` package hosts all of the simulation code. The central piece is the
`Market` class in `economy/market/market.py`. It creates agents using the job
recipes, collects their orders and resolves trades through an order book.

## Running a simulation

A short example of starting a simulation is shown below:

```python
from economy import Market

# Create a market with a handful of agents
market = Market(num_agents=9)

# Run the simulation for five days
market.simulate(5)
```

This will print out each agent's activity and the trades executed on each day.

## Setup

The project can be run inside a virtual environment to isolate its
dependencies:

```bash
# Create and activate the virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

After activating the environment, the unit tests can be executed with `pytest`.

