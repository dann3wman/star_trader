from flask import Flask, render_template, request, jsonify
import os

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

from economy import Market, SQLiteHistory, jobs, rebuild_database

# Persistent simulation support
DB_PATH = os.environ.get("STAR_TRADER_DB", "sim.db")
_history = SQLiteHistory(DB_PATH)
_persistent_market = Market(num_agents=9, history=_history)


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            num_agents = int(data.get('num_agents', 9))
            days = int(data.get('days', 1))
            initial_money = int(data.get('initial_money', 100))
            initial_inv = int(data.get('initial_inv', 10))
            job_counts = data.get('job_counts', {})
        else:
            num_agents = int(request.form.get('num_agents', 9))
            days = int(request.form.get('days', 1))
            initial_money = int(request.form.get('initial_money', 100))
            initial_inv = int(request.form.get('initial_inv', 10))
            job_counts = {}
            for key, val in request.form.items():
                if key.startswith('job_'):
                    job_name = key[4:].replace('_', ' ')
                    try:
                        count = int(val)
                    except ValueError:
                        continue
                    if count > 0:
                        job_counts[job_name] = count

        market = Market(num_agents=num_agents, job_counts=job_counts,
                        initial_inv=initial_inv, initial_money=initial_money)
        market.simulate(days)

        # Collect aggregated statistics and daily price history
        hist = market.history(days)
        results = {}
        for good in hist:
            low, high, current, ratio = market.aggregate(good, days)
            # Extract mean price for each day (may be None if no trades)
            prices = [trade.mean for trade in hist[good]]
            volumes = [trade.volume for trade in hist[good]]
            results[str(good)] = {
                'low': low,
                'high': high,
                'current': current,
                'ratio': ratio,
                'prices': prices,
                'volumes': volumes,
            }

        agent_stats = market.agent_stats()
        for agent in agent_stats:
            agent['trades'] = {str(k): v for k, v in agent['trades'].items()}
        if request.is_json or request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']:
            return jsonify({'days': days, 'results': results, 'agents': agent_stats})
        return render_template('results.html', results=results, days=days, agents=agent_stats)

    job_list = [str(j) for j in jobs.all()]
    return render_template('index.html', jobs=job_list)


def _compile_results(market):
    """Helper to build the results dict for templates/JSON."""
    days = market._history.day_number
    hist = market.history(days)
    results = {}
    for good in hist:
        low, high, current, ratio = market.aggregate(good, days)
        prices = [trade.mean for trade in hist[good]]
        volumes = [trade.volume for trade in hist[good]]
        results[str(good)] = {
            'low': low,
            'high': high,
            'current': current,
            'ratio': ratio,
            'prices': prices,
            'volumes': volumes,
        }

    agent_stats = market.agent_stats()
    for agent in agent_stats:
        agent['trades'] = {str(k): v for k, v in agent['trades'].items()}
    return {'days': days, 'results': results, 'agents': agent_stats}


@app.route('/overview', methods=['GET'])
def overview():
    """Return high level market overview for the persistent market."""
    data = _persistent_market.overview_stats()
    if request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']:
        return jsonify(data)
    return render_template('overview.html', **data)


@app.route('/agent/<path:name>', methods=['GET'])
def agent_detail(name):
    """Show detailed statistics for a single agent."""
    agent = next((a for a in _persistent_market._agents if a.name == name), None)
    if agent is None:
        return ("Agent not found", 404)
    inventory = {str(g): qty for g, qty in agent._inventory._items.items()}
    data = {
        'name': agent.name,
        'job': agent.job,
        'money': agent.money,
        'total_profit': agent.total_profit,
        'age': agent.age,
        'inventory': inventory,
        'trades': {str(k): v for k, v in agent.trade_stats.items()},
    }
    if request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']:
        return jsonify(data)
    return render_template('agent.html', **data)


@app.route('/step', methods=['POST'])
def step():
    """Advance the persistent simulation by N days."""
    if request.is_json:
        data = request.get_json()
        days = int(data.get('days', 1))
    else:
        days = int(request.form.get('days', 1))
    global _persistent_market
    _persistent_market.simulate(days)
    data = _compile_results(_persistent_market)
    if request.is_json or request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']:
        return jsonify(data)
    return render_template('results.html', **data)


@app.route('/reset', methods=['POST'])
def reset():
    """Reset the persistent simulation state."""
    if request.is_json:
        data = request.get_json()
        num_agents = int(data.get('num_agents', 9))
    else:
        num_agents = int(request.form.get('num_agents', 9))
    global _history, _persistent_market
    _history.reset()
    _persistent_market = Market(num_agents=num_agents, history=_history)
    data = _compile_results(_persistent_market)
    if request.is_json or request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']:
        return jsonify(data)
    return render_template('results.html', **data)


@app.route('/load', methods=['GET'])
def load():
    """Load an existing simulation database."""
    global _history, _persistent_market, DB_PATH
    db = request.args.get('db', DB_PATH)
    num_agents = int(request.args.get('num_agents', 9))
    DB_PATH = db
    _history = SQLiteHistory(DB_PATH)
    _persistent_market = Market(num_agents=num_agents, history=_history)
    data = _compile_results(_persistent_market)
    if request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']:
        return jsonify(data)
    return render_template('results.html', **data)


@app.route('/rebuild', methods=['POST'])
def rebuild():
    """Rebuild goods and jobs tables and reset the persistent market."""
    if request.is_json:
        data = request.get_json()
        num_agents = int(data.get('num_agents', 9))
    else:
        num_agents = int(request.form.get('num_agents', 9))
    rebuild_database()
    global _history, _persistent_market
    _history.reset()
    _persistent_market = Market(num_agents=num_agents, history=_history)
    data = _compile_results(_persistent_market)
    if request.is_json or request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']:
        return jsonify(data)
    return render_template('results.html', **data)

if __name__ == '__main__':
    app.run(debug=True)
