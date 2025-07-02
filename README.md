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
    ├── goods.py       # Load goods from the database
    ├── jobs.py        # Load jobs from the database
    ├── offer.py       # Ask/Bid definitions
    └── market/        # Market engine and order book
        ├── market.py  # `Market` class and simulation loop
        ├── book.py    # Order book matching bids and asks
        └── history.py # Tracking price history
```

### `data/`

The `data` folder contains YAML configuration files used to seed the
database. `goods.yml` lists the available goods while `jobs.yml` defines the
job recipes. On the first run the database tables are populated from these
files and subsequent runs load the definitions from SQLite.

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

### Persisting simulation data

Trade history is now persisted to a SQLite database by default. The
`simulate.py` helper script can be used to advance the stored simulation or
reset it entirely. Run `python simulate.py --step` to advance the existing
simulation by one day or `python simulate.py --reset` to start over from
scratch.

### Configuration

Runtime options such as the database path and default starting resources can be
set through environment variables:

```
STAR_TRADER_DB              # SQLite database filename (default: sim.db)
STAR_TRADER_INITIAL_MONEY   # Starting money for agents (default: 100)
STAR_TRADER_INITIAL_INV     # Starting inventory per agent (default: 10)
STAR_TRADER_INVENTORY_SIZE  # Inventory capacity for agents (default: 15)
STAR_TRADER_DAILY_TAX       # Daily tax deducted from each agent (default: 1)
```

These values are loaded on startup via `config.py` and used across the
application.

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


## Running the Flask GUI

A simple Flask application is provided in `gui/app.py`. After installing the requirements you can launch the web interface with:

```bash
python gui/app.py
```

Open your browser at [http://localhost:5000](http://localhost:5000) to configure and run a simulation.

The results page now includes a table showing the average price of each good for every simulated day, allowing you to track price trends over time.
It also lists statistics for each agent, including their final money and total profit, so you can compare how well different strategies performed. An additional table breaks down how many units of each good every agent bought and sold during the run. The price and volume charts on this page are rendered with **Plotly** so you can hover and zoom for a closer look at the data.

## Plugins

Modules placed in the top-level `plugins` package are loaded automatically when a `Market` instance is created. Plugins can define additional `Good` and `Job` objects or register custom `Agent` subclasses via `economy.plugins.register_agent` to extend the simulation.

See **REFACTORING.md** for ideas on improving the codebase.
