import os
import pandas as pd
import pyotp
from SmartApi import SmartConnect
from datetime import datetime, timedelta
import streamlit as st

# ------------------ CONFIG ------------------ #
API_KEY = os.getenv("API_KEY")
CLIENT_ID = os.getenv("CLIENT_ID")
PASSWORD = os.getenv("PASSWORD")
TOTP_SECRET = os.getenv("TOTP_SECRET")

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")  # For Render env
obj = SmartConnect(api_key=API_KEY)
obj.setAccessToken(ACCESS_TOKEN)

# -------------- FETCH HISTORICAL DATA -------------- #
def get_historical_data(symbol, from_date, to_date, interval="FIFTEEN_MINUTE"):
    try:
        params = {
            "exchange": "NSE",
            "symboltoken": symbol,
            "interval": interval,
            "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
            "todate": to_date.strftime("%Y-%m-%d %H:%M")
        }
        data = obj.getCandleData(params)
        df = pd.DataFrame(data['data'], columns=["datetime","open","high","low","close","volume"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        return df
    except:
        return pd.DataFrame()

# -------------- DETECT BOUNCE PATTERN -------------- #
def detect_bounce(df):
    df["SMA20"] = df["close"].rolling(20).mean()
    df["SMA50"] = df["close"].rolling(50).mean()

    results = []
    last_bounce_20 = None
    last_bounce_50 = None

    for i in range(50, len(df)):
        row = df.iloc[i]
        if row["close"] > row["open"]:  # Green candle
            # Check if candle touched SMA20 or SMA50
            bounce_20 = row["low"] <= row["SMA20"] <= row["high"]
            bounce_50 = row["low"] <= row["SMA50"] <= row["high"]

            if bounce_20:
                if last_bounce_20 is None or row["low"] > last_bounce_20:
                    results.append(row["datetime"])
                    last_bounce_20 = row["low"]

            if bounce_50:
                if last_bounce_50 is None or row["low"] > last_bounce_50:
                    results.append(row["datetime"])
                    last_bounce_50 = row["low"]
    return results

# -------------- STREAMLIT UI -------------- #
st.title("📈 Intraday Bounce Scanner")

mode = st.radio("Select Mode", ["Live Mode", "Backtest Mode"])

if mode == "Backtest Mode":
    from_date = st.date_input("From Date", datetime.now() - timedelta(days=7))
    to_date = st.date_input("To Date", datetime.now())

    if st.button("Run Backtest"):
        stocks = ["ICICIBANK-EQ", "TCS-EQ", "HDFCBANK-EQ"]  # You can add more
        final_results = []

        for stock in stocks:
            df = get_historical_data(stock, from_date, to_date)
            if df.empty:
                continue
            bounces = detect_bounce(df)
            if bounces:
                dates = [d.strftime("%d-%b") for d in bounces]
                final_results.append({"Stock": stock, "Bounce Count": len(bounces), "Bounce Dates": ", ".join(dates)})

        if final_results:
            result_df = pd.DataFrame(final_results)
            st.dataframe(result_df)

            # Export to CSV
            csv = result_df.to_csv(index=False)
            st.download_button("📥 Download CSV", csv, "backtest_results.csv", "text/csv")
        else:
            st.warning("⚠️ No bounce patterns found in this date range!")

else:
    st.info("Live Mode is under setup. It will fetch latest data with bounce detection.")
