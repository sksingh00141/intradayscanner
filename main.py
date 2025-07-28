import os
import pandas as pd
import datetime as dt
from SmartApi import SmartConnect
import pyotp

# 🔹 Take credentials from Render environment variables
API_KEY = os.getenv("API_KEY")
CLIENT_ID = os.getenv("CLIENT_ID")
PASSWORD = os.getenv("PASSWORD")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")  # ✅ Access Token from Render Env

# 🔹 Connect to AngelOne API
obj = SmartConnect(api_key=API_KEY)
obj.setAccessToken(ACCESS_TOKEN)

# 🔹 Fetch historical data function
def fetch_historical(symbol_token, interval, from_date, to_date):
    params = {
        "exchange": "NSE",
        "symboltoken": symbol_token,
        "interval": interval,
        "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
        "todate": to_date.strftime("%Y-%m-%d %H:%M"),
    }
    return obj.getCandleData(params)

# 🔹 Bounce detection function
def is_bounce(df):
    df["SMA20"] = df["close"].rolling(20).mean()
    df["SMA50"] = df["close"].rolling(50).mean()

    bounces = []
    for i in range(50, len(df)):
        candle = df.iloc[i]
        prev = df.iloc[i - 1]

        if candle["close"] > candle["open"] and (
            candle["low"] <= candle["SMA20"] <= candle["close"]
            or candle["low"] <= candle["SMA50"] <= candle["close"]
        ):
            if candle["SMA20"] > prev["SMA20"] and candle["SMA50"] > prev["SMA50"]:
                bounces.append(df.iloc[i])

    return bounces

# 🔹 Example usage
if __name__ == "__main__":
    symbol_token = "3045"  # Example: ICICI Bank token
    from_date = dt.datetime.now() - dt.timedelta(days=10)
    to_date = dt.datetime.now()

    data = fetch_historical(symbol_token, "FIFTEEN_MINUTE", from_date, to_date)

    if "data" in data:
        candles = data["data"]
        df = pd.DataFrame(candles, columns=["datetime", "open", "high", "low", "close", "volume"])
        df["datetime"] = pd.to_datetime(df["datetime"])

        results = is_bounce(df)
        for r in results:
            print(r)
    else:
        print("Error fetching data:", data)
