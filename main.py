from flask import Flask, jsonify, send_from_directory
from stockmaster import get_5min_data
from intradaybreakoutengine import breakout_score
from intradayboostengine import boost_score

app = Flask(__name__)

# तुझी watchlist इथे बदलू शकतोस
WATCHLIST = ["APOLLOHOSP", "VOLTAS", "OFSS", "PAYTM", "TATATECH"]

@app.route('/')
def home():
    return send_from_directory('.', 'fodashboard.html')


@app.route('/api/breakout')
def breakout():
    results = []

    for symbol in WATCHLIST:
        try:
            df = get_5min_data(symbol)
            bs = breakout_score(df)
            results.append({
                "symbol": symbol,
                "bs": bs
            })
        except Exception as e:
            results.append({
                "symbol": symbol,
                "bs": 0,
                "error": str(e)
            })

    results = sorted(results, key=lambda x: x['bs'], reverse=True)
    return jsonify(results)


@app.route('/api/boost')
def boost():
    results = []

    for symbol in WATCHLIST:
        try:
            df = get_5min_data(symbol)
            bs = breakout_score(df)

            # temporary RF logic (नंतर improve करू)
            rf = bs / 2

            bscore = boost_score(rf, bs)

            results.append({
                "symbol": symbol,
                "boost": bscore
            })
        except Exception as e:
            results.append({
                "symbol": symbol,
                "boost": 0,
                "error": str(e)
            })

    results = sorted(results, key=lambda x: x['boost'], reverse=True)
    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
