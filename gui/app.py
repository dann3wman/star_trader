from flask import Flask, render_template, request, redirect, url_for

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
from economy.market.history import SQLiteHistory

app = Flask(__name__)
app.config['DB_PATH'] = 'sim.db'


def _render_results(history, agents=None):
    days = history.day_number
    hist = history.history(days)
    results = {}
    for good in hist:
        low, high, current, ratio = history.aggregate(good, days)
        prices = [trade.mean for trade in hist[good]]
        results[good] = {
            'low': low,
            'high': high,
            'current': current,
            'ratio': ratio,
            'prices': prices,
        }
    return render_template('results.html', results=results, days=days, agents=agents)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/step', methods=['POST'])
def step():
    num_agents = int(request.form.get('num_agents', 9))
    days = int(request.form.get('days', 1))
    history = SQLiteHistory(db_path=app.config['DB_PATH'])
    market = Market(num_agents=num_agents, history=history)
    market.simulate(days)
    agent_stats = market.agent_stats()
    return _render_results(history, agent_stats)


@app.route('/results')
def results():
    history = SQLiteHistory(db_path=app.config['DB_PATH'])
    return _render_results(history)


@app.route('/reset', methods=['POST'])
def reset():
    history = SQLiteHistory(db_path=app.config['DB_PATH'])
    history.reset()
    return redirect(url_for('index'))


if __name__ == '__main__':  # pragma: no cover - manual invocation
    app.run(debug=True)
