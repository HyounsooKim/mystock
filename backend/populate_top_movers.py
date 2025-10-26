"""Manual script to populate Cosmos DB with top movers data.

This script directly calls Alpha Vantage and saves to Cosmos DB,
bypassing Azure Functions for initial data population.
"""

import os
import sys
from pathlib import Path

# Add backend src to path
backend_src = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(backend_src))

import asyncio
from datetime import datetime, timezone
from azure.cosmos import CosmosClient, PartitionKey, exceptions
import requests

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def fetch_top_movers():
    """Fetch from Alpha Vantage."""
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    url = f"https://www.alphavantage.co/query?function=TOP_GAINERS_LOSERS&apikey={api_key}"
    
    print(f"Fetching data from Alpha Vantage...")
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    print(f"✓ Fetched {len(data.get('top_gainers', []))} gainers")
    print(f"✓ Fetched {len(data.get('top_losers', []))} losers")
    print(f"✓ Fetched {len(data.get('most_actively_traded', []))} active")
    
    return data

def save_to_cosmos(data):
    """Save to Cosmos DB."""
    endpoint = os.getenv("COSMOS_ENDPOINT")
    key = os.getenv("COSMOS_KEY")
    database_name = os.getenv("COSMOS_DATABASE_NAME")
    
    print(f"\nConnecting to Cosmos DB: {endpoint}")
    
    # For local emulator
    connection_verify = True
    if "localhost" in endpoint:
        connection_verify = False
        print("Using local Cosmos DB emulator")
    
    client = CosmosClient(url=endpoint, credential=key, connection_verify=connection_verify)
    database = client.get_database_client(database_name)
    
    # Create container if needed
    try:
        container = database.create_container_if_not_exists(
            id="top_movers",
            partition_key=PartitionKey(path="/date"),
            offer_throughput=400
        )
        print("✓ Container 'top_movers' ready")
    except exceptions.CosmosHttpResponseError as e:
        print(f"✗ Error creating container: {e}")
        raise
    
    # Prepare document
    now = datetime.now(timezone.utc)
    timestamp = now.isoformat()
    date_str = now.strftime("%Y-%m-%d")
    
    document = {
        "id": f"top-movers-{timestamp}",
        "date": date_str,
        "timestamp": timestamp,
        "data": {
            "top_gainers": data.get("top_gainers", [])[:20],
            "top_losers": data.get("top_losers", [])[:20],
            "most_actively_traded": data.get("most_actively_traded", [])[:20]
        },
        "metadata": {
            "last_updated": data.get("last_updated", ""),
            "record_count": {
                "gainers": len(data.get("top_gainers", [])),
                "losers": len(data.get("top_losers", [])),
                "active": len(data.get("most_actively_traded", []))
            }
        }
    }
    
    # Save
    try:
        container.create_item(body=document)
        print(f"✓ Saved document: {document['id']}")
        print(f"  Date: {date_str}")
        print(f"  Timestamp: {timestamp}")
    except exceptions.CosmosHttpResponseError as e:
        print(f"✗ Error saving: {e}")
        raise

if __name__ == "__main__":
    print("=" * 60)
    print("Manual Top Movers Data Population")
    print("=" * 60)
    
    try:
        # Fetch from API
        data = fetch_top_movers()
        
        # Save to Cosmos DB
        save_to_cosmos(data)
        
        print("\n" + "=" * 60)
        print("SUCCESS! Data saved to Cosmos DB")
        print("=" * 60)
        print("\nYou can now test the API:")
        print("  curl http://localhost:8000/api/v1/stocks/top-movers")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        sys.exit(1)
