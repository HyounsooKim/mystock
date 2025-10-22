"""Test script for Alpha Vantage API service."""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import directly to avoid circular imports
import requests
from datetime import datetime
from enum import Enum

class Period(str, Enum):
    """Time period for candlestick data."""
    THIRTY_MIN = "30m"
    ONE_HOUR = "1h"
    ONE_DAY = "1d"
    ONE_WEEK = "1wk"
    ONE_MONTH = "1mo"

def test_alpha_vantage():
    """Test Alpha Vantage API integration."""
    
    service = AlphaVantageService()
    
    print("=" * 60)
    print("Testing Alpha Vantage API Service")
    print("=" * 60)
    
    # Test 1: Get quote for IBM
    print("\n1. Testing Quote API for IBM...")
    quote = service.get_quote('IBM')
    if quote:
        print(f"✅ Success!")
        print(f"   Symbol: {quote['symbol']}")
        print(f"   Price: ${quote['current_price']:.2f}")
        print(f"   Change: {quote['daily_change_pct']:.2f}%")
        print(f"   Volume: {quote['volume']:,}")
    else:
        print("❌ Failed to get quote")
    
    # Test 2: Get quote for AAPL
    print("\n2. Testing Quote API for AAPL...")
    quote = service.get_quote('AAPL')
    if quote:
        print(f"✅ Success!")
        print(f"   Symbol: {quote['symbol']}")
        print(f"   Price: ${quote['current_price']:.2f}")
        print(f"   Change: {quote['daily_change_pct']:.2f}%")
    else:
        print("❌ Failed to get quote")
    
    # Test 3: Search for symbols
    print("\n3. Testing Symbol Search for 'Microsoft'...")
    results = service.search_symbol('Microsoft')
    if results:
        print(f"✅ Success! Found {len(results)} results:")
        for i, result in enumerate(results[:3], 1):
            print(f"   {i}. {result['symbol']} - {result['name']} ({result['region']})")
    else:
        print("❌ Failed to search symbols")
    
    # Test 4: Get candlestick data
    print("\n4. Testing Candlestick Data for IBM (Daily)...")
    candles = service.get_candlestick_data('IBM', Period.ONE_DAY)
    if candles:
        print(f"✅ Success! Retrieved {len(candles)} data points")
        if candles:
            latest = candles[0]
            print(f"   Latest: {latest['timestamp'].strftime('%Y-%m-%d')}")
            print(f"   Open: ${latest['open']:.2f}, Close: ${latest['close']:.2f}")
            print(f"   High: ${latest['high']:.2f}, Low: ${latest['low']:.2f}")
    else:
        print("❌ Failed to get candlestick data")
    
    # Test 5: Get news
    print("\n5. Testing News API for AAPL...")
    news = service.get_news('AAPL', limit=5)
    if news:
        print(f"✅ Success! Retrieved {len(news)} news articles:")
        for i, article in enumerate(news[:3], 1):
            print(f"   {i}. {article['title'][:60]}...")
            print(f"      Sentiment: {article['overall_sentiment_label']} ({article['overall_sentiment_score']:.2f})")
    else:
        print("❌ Failed to get news")
    
    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)

if __name__ == '__main__':
    test_alpha_vantage()
