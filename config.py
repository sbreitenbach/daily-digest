# --- API KEYS (REPLACE WITH YOURS) ---
GEMINI_API_KEY = ""
FINNHUB_API_KEY = ""

# --- EMAIL SETTINGS (REPLACE WITH YOURS) ---
# For Gmail, you'll need to generate an "App Password" if you have 2-Factor Auth enabled.
SMTP_SERVER = ""
SMTP_PORT = 587
EMAIL_SENDER = ""
EMAIL_PASSWORD = ""
EMAIL_RECEIVER = "" # Can be the same as sender

# --- CUSTOMIZE YOUR DIGEST ---

# Add your specific National Weather Service (NWS) forecast URL here.
NWS_FORECAST_URL = ""

# Section for Reddit communities (using the .json endpoint)
REDDIT_JSON_FEEDS = {
    "Funny": "https://www.reddit.com/r/funny/top/.json?t=day",
}

# Section for standard RSS feeds (from news sites, blogs, etc.)
GENERAL_RSS_FEEDS = {
    "NPR": "https://feeds.npr.org/1001/rss.xml", 
}


# Section for financial data. Use symbols from Finnhub.

FINANCIAL_ASSETS = {
    "S&P 500": "SPY",
    "Bitcoin": "BINANCE:BTCUSDT",
}
