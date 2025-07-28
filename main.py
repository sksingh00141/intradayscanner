import yfinance as yf
import pandas as pd
import ta
from datetime import datetime, timedelta
from flask import Flask, request, render_template_string
import os

app = Flask(__name__)

# Nifty 500 list – add more symbols if needed
NIFTY_500 = [
    "ICICIBANK.NS", "TORNTPHARM.NS", "HDFCBANK.NS", "RELIANCE.NS", "TCS.NS"
]

def get_bounce_stocks(timeframe, backtest_bars=50):
    results = []
    for symbol in NIFTY_500:
        try:
            interval = "15m" if timeframe == "15min" else "30m"
            data = yf.download(symbol, period="7d", interval=interval, progress=False)

            if data is None or len(data) < 60:
                continue

            df = data.copy()
            df.dropna(inplace=True)

            df['sma20'] = ta.trend.sma_indicator(df['Close'], window=20)
            df['sma50'] = ta.trend.sma_indicator(df['Close'], window=50)
            df['sma20_slope'] = df['sma20'].diff()
            df['sma50_slope'] = df['sma50'].diff()

            bounces = {'20': [], '50': []}
            for i in range(len(df) - backtest_bars, len(df)):
                row = df.iloc[i]

                is_green = row['Close'] > row['Open']
                touch_20 = row['Low'] <= row['sma20'] <= row['High']
                touch_50 = row['Low'] <= row['sma50'] <= row['High']
                sma20_up = row['sma20_slope'] > 0
                sma50_up = row['sma50_slope'] > 0

                if not is_green:
                    continue

                # Bounce on 20 SMA
                if touch_20 and sma20_up:
                    if len(bounces['20']) == 0 or row['Low'] > bounces['20'][-1]['low']:
                        bounces['20'].append({'index': df.index[i], 'low': row['Low']})

                # Bounce on 50 SMA
                if touch_50 and sma50_up:
                    if len(bounces['50']) == 0 or row['Low'] > bounces['50'][-1]['low']:
                        bounces['50'].append({'index': df.index[i], 'low': row['Low']})

            total_bounces = len(bounces['20']) + len(bounces['50'])
            if total_bounces >= 2:
                last = df.iloc[-1]
                result = {
                    'symbol': symbol,
                    'time': df.index[-1].strftime('%Y-%m-%d %H:%M'),
                    'price': round(last['Close'], 2),
                    'link': f'https://www.tradingview.com/chart/?symbol=NSE:{symbol.replace(".NS", "")}'
                }
                results.append(result)

        except Exception as e:
            print(f"Error in {symbol}: {e}")
            continue

    return results

@app.route('/')
def index():
    timeframe = request.args.get('timeframe', '15min')
    data = get_bounce_stocks(timeframe)
    return render_template_string("""
    <html>
    <head><title>Bounce Scanner</title></head>
    <body style="font-family:Arial">
        <h2>📈 Intraday Bounce Scanner ({{ timeframe }})</h2>
        <a href="/?timeframe=15min">15min</a> | 
        <a href="/?timeframe=30min">30min</a><br><br>
        <table border="1" cellpadding="6" cellspacing="0">
            <tr>
                <th>Symbol</th><th>Time</th><th>Price</th><th>Chart</th>
            </tr>
            {% for row in data %}
            <tr>
                <td>{{ row.symbol }}</td>
                <td>{{ row.time }}</td>
                <td>{{ row.price }}</td>
                <td><a href="{{ row.link }}" target="_blank">View</a></td>
            </tr>
            {% endfor %}
        </table>
        {% if not data %}
        <p>No results found.</p>
        {% endif %}
    </body>
    </html>
    """, data=data, timeframe=timeframe)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
