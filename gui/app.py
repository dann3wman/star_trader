from flask import Flask, render_template, request

from economy import Market

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        num_agents = int(request.form.get('num_agents', 9))
        days = int(request.form.get('days', 1))
        market = Market(num_agents=num_agents)
        market.simulate(days)
        results = {}
        for good in market.history():
            low, high, current, ratio = market.aggregate(good)
            results[good] = {
                'low': low,
                'high': high,
                'current': current,
                'ratio': ratio,
            }
        return render_template('results.html', results=results, days=days)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
