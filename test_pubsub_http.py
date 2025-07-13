#!/usr/bin/env python3
"""
Test script to verify Pub/Sub access using HTTP API calls instead of client library.
"""
import os
import json
import aiohttp
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials from environment  
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
ACCESS_TOKEN = os.getenv("NEST_ACCESS_TOKEN")

async def test_pubsub_http_api():
    """Test Pub/Sub using direct HTTP API calls."""
    print("Testing Pub/Sub via HTTP API...")
    
    # Test listing topics
    topics_url = f"https://pubsub.googleapis.com/v1/projects/{GCP_PROJECT_ID}/topics"
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    async with aiohttp.ClientSession() as session:
        print(f"\nTesting topics endpoint: {topics_url}")
        async with session.get(topics_url, headers=headers) as response:
            print(f"Topics response status: {response.status}")
            topics_data = await response.json()
            print("Topics response:")
            print(json.dumps(topics_data, indent=2))
            
        # Test listing subscriptions
        subs_url = f"https://pubsub.googleapis.com/v1/projects/{GCP_PROJECT_ID}/subscriptions"
        print(f"\nTesting subscriptions endpoint: {subs_url}")
        async with session.get(subs_url, headers=headers) as response:
            print(f"Subscriptions response status: {response.status}")
            subs_data = await response.json()
            print("Subscriptions response:")
            print(json.dumps(subs_data, indent=2))
            
        # Test publishing a test message
        publish_url = f"https://pubsub.googleapis.com/v1/projects/{GCP_PROJECT_ID}/topics/nest-events:publish"
        test_message = {
            "messages": [
                {
                    "data": "VGVzdCBtZXNzYWdl",  # Base64 encoded "Test message"
                    "attributes": {
                        "source": "test"
                    }
                }
            ]
        }
        print(f"\nTesting publish endpoint: {publish_url}")
        async with session.post(publish_url, headers=headers, json=test_message) as response:
            print(f"Publish response status: {response.status}")
            publish_data = await response.json()
            print("Publish response:")
            print(json.dumps(publish_data, indent=2))

if __name__ == '__main__':
    asyncio.run(test_pubsub_http_api())
