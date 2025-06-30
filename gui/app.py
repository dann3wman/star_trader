from flask import Flask, render_template, request

from economy.market.history import SQLiteHistory

# Ensure the project root is on the Python path when running this module
# directly (e.g. `python gui/app.py`). This allows imports like
# `from economy import Market` to succeed even if the current working
# directory is the `gui/` folder.
if __package__ is None:  # pragma: no cover - executed only when run directly
    import sys
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from economy import Market

# Use a persistent SQLite database to store simulation history
history = SQLiteHistory()

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'reset' in request.form:
            history.reset()
            return render_template('index.html', message='Simulation reset.')

        num_agents = int(request.form.get('num_agents', 9))
        days = int(request.form.get('days', 1))
        market = Market(num_agents=num_agents, history=history)
        market.simulate(days)

        # Collect aggregated statistics and daily price history
        hist = history.history(days)
        results = {}
        for good in hist:
            low, high, current, ratio = history.aggregate(good, days)
            # Extract mean price for each day (may be None if no trades)
            prices = [trade.mean for trade in hist[good]]
            results[good] = {
                'low': low,
                'high': high,
                'current': current,
                'ratio': ratio,
                'prices': prices,
            }

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
