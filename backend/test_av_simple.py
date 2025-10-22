"""Simple Alpha Vantage API test without dependencies."""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
USE_DELAYED = os.getenv("ALPHA_VANTAGE_USE_DELAYED", "true").lower() in ("true", "1", "yes")
BASE_URL = "https://www.alphavantage.co/query"

print(f"Using API Key: {API_KEY[:10]}..." if API_KEY else "No API Key found!")
print(f"Delayed Mode: {'YES (15min delay, higher rate limit)' if USE_DELAYED else 'NO (realtime, lower rate limit)'}")
print("-" * 60)

# Test 1: Get Quote for IBM
print("\n1. Testing Global Quote for IBM:")
params = {
    "function": "GLOBAL_QUOTE",
    "symbol": "IBM",
    "apikey": API_KEY
}
if USE_DELAYED:
    params["entitlement"] = "delayed"

response = requests.get(BASE_URL, params=params)
data = response.json()
print(f"Status: {response.status_code}")

# Handle both realtime and delayed response keys
quote = data.get("Global Quote") or data.get("Global Quote - DATA DELAYED BY 15 MINUTES")

if quote:
    print(f"✅ IBM Price: ${quote.get('05. price', 'N/A')}")
    print(f"   Change: {quote.get('10. change percent', 'N/A')}")
else:
    print(f"❌ Error or Rate Limit: {data.get('Note', data.get('Error Message', 'Unknown'))}")

print("-" * 60)

# Test 2: Get Quote for AAPL
print("\n2. Testing Global Quote for AAPL:")
params = {
    "function": "GLOBAL_QUOTE",
    "symbol": "AAPL",
    "apikey": API_KEY
}
if USE_DELAYED:
    params["entitlement"] = "delayed"

response = requests.get(BASE_URL, params=params)
data = response.json()
print(f"Status: {response.status_code}")

# Handle both realtime and delayed response keys
quote = data.get("Global Quote") or data.get("Global Quote - DATA DELAYED BY 15 MINUTES")

if quote:
    print(f"✅ AAPL Price: ${quote.get('05. price', 'N/A')}")
    print(f"   Change: {quote.get('10. change percent', 'N/A')}")
else:
    print(f"❌ Error or Rate Limit: {data.get('Note', data.get('Error Message', 'Unknown'))}")

print("-" * 60)

# Test 3: Symbol Search
print("\n3. Testing Symbol Search for 'Microsoft':")
params = {
    "function": "SYMBOL_SEARCH",
    "keywords": "Microsoft",
    "apikey": API_KEY
}
if USE_DELAYED:
    params["entitlement"] = "delayed"

response = requests.get(BASE_URL, params=params)
data = response.json()
print(f"Status: {response.status_code}")
if "bestMatches" in data:
    matches = data["bestMatches"][:3]  # Show first 3
    print(f"✅ Found {len(data['bestMatches'])} matches (showing top 3):")
    for match in matches:
        print(f"   - {match.get('1. symbol')}: {match.get('2. name')}")
else:
    print(f"❌ Error: {data.get('Note', data.get('Error Message', 'Unknown'))}")

print("-" * 60)

# Test 4: Daily Candlestick Data
print("\n4. Testing Daily Time Series for IBM:")
params = {
    "function": "TIME_SERIES_DAILY",
    "symbol": "IBM",
    "apikey": API_KEY
}
if USE_DELAYED:
    params["entitlement"] = "delayed"

response = requests.get(BASE_URL, params=params)
data = response.json()
print(f"Status: {response.status_code}")
if "Time Series (Daily)" in data:
    time_series = data["Time Series (Daily)"]
    latest_date = list(time_series.keys())[0]
    latest_data = time_series[latest_date]
    print(f"✅ Latest data ({latest_date}):")
    print(f"   Open: ${latest_data.get('1. open')}")
    print(f"   High: ${latest_data.get('2. high')}")
    print(f"   Low: ${latest_data.get('3. low')}")
    print(f"   Close: ${latest_data.get('4. close')}")
    print(f"   Volume: {latest_data.get('5. volume')}")
else:
    print(f"❌ Error: {data.get('Note', data.get('Error Message', 'Unknown'))}")

print("-" * 60)

# Test 5: News Sentiment
print("\n5. Testing News & Sentiment for AAPL:")
params = {
    "function": "NEWS_SENTIMENT",
    "tickers": "AAPL",
    "limit": 5,
    "apikey": API_KEY
}
if USE_DELAYED:
    params["entitlement"] = "delayed"

response = requests.get(BASE_URL, params=params)
data = response.json()
print(f"Status: {response.status_code}")
if "feed" in data:
    news = data["feed"][:2]  # Show first 2 articles
    print(f"✅ Found {len(data['feed'])} articles (showing top 2):")
    for article in news:
        print(f"\n   Title: {article.get('title', 'N/A')[:80]}...")
        print(f"   Published: {article.get('time_published', 'N/A')}")
        if article.get('ticker_sentiment'):
            for sentiment in article['ticker_sentiment'][:1]:
                print(f"   Sentiment: {sentiment.get('ticker_sentiment_label', 'N/A')} ({sentiment.get('ticker_sentiment_score', 'N/A')})")
else:
    print(f"❌ Error: {data.get('Note', data.get('Error Message', 'Unknown'))}")

print("\n" + "=" * 60)
print("Test completed!")
print("=" * 60)
