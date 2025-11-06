"""Azure Functions app for MyStock Top Movers updater.

This uses Azure Functions Python v2 programming model which supports Python 3.11.
"""

import azure.functions as func
import logging
import os
from datetime import datetime, timezone
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from azure.identity import DefaultAzureCredential
import aiohttp

app = func.FunctionApp()

logger = logging.getLogger(__name__)


async def fetch_top_movers_from_api():
    """Fetch top movers data from Alpha Vantage API."""
    api_key = os.environ.get("ALPHA_VANTAGE_API_KEY", "demo")
    url = f"https://www.alphavantage.co/query?function=TOP_GAINERS_LOSERS&apikey={api_key}"
    
    logger.info(f"Fetching top movers from Alpha Vantage API")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                logger.error(f"API request failed with status {response.status}")
                raise Exception(f"API request failed: {response.status}")
            
            data = await response.json()
            
            if "Error Message" in data:
                logger.error(f"API error: {data['Error Message']}")
                raise Exception(f"API error: {data['Error Message']}")
            
            if "Note" in data:
                logger.warning(f"API note: {data['Note']}")
            
            logger.info("Successfully fetched top movers data")
            return data


def save_to_cosmos(data: dict):
    """Save top movers data to Cosmos DB using Managed Identity."""
    endpoint = os.environ.get("COSMOS_ENDPOINT")
    database_name = os.environ.get("COSMOS_DATABASE_NAME")
    
    logger.info(f"Connecting to Cosmos DB: {endpoint}")
    
    # Determine if running locally based on endpoint
    is_local = bool(endpoint and ("localhost" in endpoint.lower() or "127.0.0.1" in endpoint))
    
    # Configure authentication credential
    try:
        credential = None
        
        if is_local:
            logger.warning("Detected localhost endpoint")
            # For local development, try key-based auth first
            key = os.environ.get("COSMOS_KEY")
            if key:
                logger.info("Using key-based authentication for local development")
                credential = key
            else:
                logger.info("No COSMOS_KEY found, attempting Azure credential")
        
        # Use DefaultAzureCredential if no key-based credential was set
        if credential is None:
            logger.info("Using managed identity authentication (DefaultAzureCredential)")
            credential = DefaultAzureCredential()
            
    except Exception as e:
        logger.error(f"Failed to initialize Azure credentials: {e}")
        raise
    
    # Configure SSL verification
    connection_verify = not is_local
    if is_local:
        logger.warning("SSL verification disabled for localhost")
    
    client = CosmosClient(
        url=endpoint,
        credential=credential,
        connection_verify=connection_verify
    )
    
    database = client.get_database_client(database_name)
    
    try:
        container = database.create_container_if_not_exists(
            id="top_movers",
            partition_key=PartitionKey(path="/date"),
            offer_throughput=400
        )
        logger.info("Container 'top_movers' ready")
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error creating container: {e}")
        raise
    
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
    
    try:
        container.create_item(body=document)
        logger.info(f"Successfully saved top movers data: {document['id']}")
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error saving to Cosmos DB: {e}")
        raise


@app.timer_trigger(schedule="0 0 * * * *", arg_name="mytimer", run_on_startup=False)
async def top_movers_updater(mytimer: func.TimerRequest) -> None:
    """Timer trigger function that runs every hour to update top movers data.
    
    Schedule: 0 0 * * * * (every hour at minute 0)
    For testing: 0 */5 * * * * (every 5 minutes)
    """
    utc_timestamp = datetime.now(timezone.utc).isoformat()
    
    if mytimer.past_due:
        logger.info('Timer is past due!')
    
    logger.info(f'Top Movers Updater executed at {utc_timestamp}')
    
    try:
        data = await fetch_top_movers_from_api()
        save_to_cosmos(data)
        logger.info('Top movers data successfully updated')
    except Exception as e:
        logger.error(f'Error updating top movers: {str(e)}')
        raise
