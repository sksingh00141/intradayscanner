import yfinance as yf
import pandas as pd
from flask import Flask, request, send_file, render_template_string
from io import BytesIO
import os

app = Flask(__name__)

NIFTY_500 = ["ICICIBANK.NS", "TORNTPHARM.NS", "HDFCBANK.NS", "RELIANCE.NS", "TCS.NS"]

def get_bounce_stocks(timeframe, backtest_date=None):
    results = []
    for symbol in NIFTY_500:
        try:
            interval = "15m" if timeframe == "15min" else "30m"
            data = yf.download(symbol, period="7d", interval=interval, progress=False)
            if data is None or len(data) < 60:
                continue

            df = data.copy().dropna()
            df["sma20"] = df["Close"].rolling(20).mean()
            df["sma50"] = df["Close"].rolling(50).mean()

            bounces = {"20": [], "50": []}

            for i in range(len(df)):
                row = df.iloc[i]

                # If backtesting, only consider selected date
                if backtest_date and row.name.strftime("%Y-%m-%d") != backtest_date:
                    continue

                # Conditions
                green = row["Close"] > row["Open"]
                touch20 = row["Low"] <= row["sma20"] <= row["Close"]
                touch50 = row["Low"] <= row["sma50"] <= row["Close"]
                body_touch20 = row["sma20"] <= row["Close"]
                body_touch50 = row["sma50"] <= row["Close"]

                # SMA alignment
                if row["sma20"] <= row["sma50"]:
                    continue

                if not green:
                    continue

                if touch20 and body_touch20:
                    if len(bounces["20"]) == 0 or row["Low"] > bounces["20"][-1]["low"]:
                        bounces["20"].append({"low": row["Low"], "time": row.name})

                if touch50 and body_touch50:
                    if len(bounces["50"]) == 0 or row["Low"] > bounces["50"][-1]["low"]:
                        bounces["50"].append({"low": row["Low"], "time": row.name})

            total_bounces = len(bounces["20"]) + len(bounces["50"])
            if total_bounces >= 3:
                last = df.iloc[-1]
                results.append({
                    "symbol": symbol,
                    "time": df.index[-1].strftime("%Y-%m-%d %H:%M"),
                    "price": round(last["Close"], 2),
                    "link": f"https://www.tradingview.com/chart/?symbol=NSE:{symbol.replace('.NS','')}"
                })
        except:
            continue
    return results

@app.route("/")
def index():
    timeframe = request.args.get("timeframe", "15min")
    date = request.args.get("date")
    data = get_bounce_stocks(timeframe, backtest_date=date)

    html = """
    <html><head><title>Bounce Scanner</title></head>
    <body style="font-family:Arial;">
        <h2>📈 Bounce Scanner ({{ timeframe }})</h2>
        <form method="get">
            <input type="hidden" name="timeframe" value="{{ timeframe }}">
            Select Date: <input type="date" name="date" value="{{ date }}">
            <button type="submit">Backtest</button>
        </form>
        <a href="/?timeframe=15min">15min</a> |
        <a href="/?timeframe=30min">30min</a> |
        <a href="/export?timeframe={{ timeframe }}&date={{ date }}">Export CSV</a>
        <hr>
        <table border="1" cellpadding="6">
            <tr><th>Symbol</th><th>Time</th><th>Price</th><th>Chart</th></tr>
            {% for row in data %}
            <tr>
                <td>{{ row.symbol }}</td>
                <td>{{ row.time }}</td>
                <td>{{ row.price }}</td>
                <td><a href="{{ row.link }}" target="_blank">View</a></td>
            </tr>
            {% endfor %}
        </table>
        {% if not data %}<p>No results found.</p>{% endif %}
    </body></html>
    """
    return render_template_string(html, timeframe=timeframe, data=data, date=date)

@app.route("/export")
def export():
    timeframe = request.args.get("timeframe", "15min")
    date = request.args.get("date")
    data = get_bounce_stocks(timeframe, backtest_date=date)

    df = pd.DataFrame(data)
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)

    return send_file(output, mimetype="text/csv", as_attachment=True, download_name="scanner_results.csv")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
