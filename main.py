import os
import pandas as pd
from SmartApi import SmartConnect

# ✅ API credentials from environment variables
API_KEY = os.getenv("API_KEY")              # Add API_KEY in Render environment variables
CLIENT_ID = os.getenv("CLIENT_ID")          # Add CLIENT_ID in Render environment variables
PASSWORD = os.getenv("PASSWORD")            # Add PASSWORD in Render environment variables
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")    # Add ACCESS_TOKEN in Render environment variables

# ✅ Initialize SmartConnect
obj = SmartConnect(api_key=API_KEY)
obj.setAccessToken(ACCESS_TOKEN)

# 🔹 Example function to fetch historical data
def get_historical_data(symboltoken, interval, fromdate, todate):
    try:
        params = {
            "exchange": "NSE",
            "symboltoken": symboltoken,
            "interval": interval,
            "fromdate": fromdate,
            "todate": todate
        }
        data = obj.getCandleData(params)
        df = pd.DataFrame(data["data"], columns=["date", "open", "high", "low", "close", "volume"])
        return df
    except Exception as e:
        print("Error fetching data:", e)
        return None

# 🔹 Example usage
if __name__ == "__main__":
    symboltoken = "3045"  # Example token (RELIANCE)
    df = get_historical_data(symboltoken, "FIFTEEN_MINUTE", "2025-07-15 09:15", "2025-07-26 15:30")
    
    if df is not None:
        print(df.head())
    else:
        print("No data received")
