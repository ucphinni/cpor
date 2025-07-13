#!/usr/bin/env python3
"""
Test script to verify Nest API access.
"""
import os
import json
import aiohttp
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials from environment
NEST_PROJECT_ID = os.getenv("NEST_PROJECT_ID")
ACCESS_TOKEN = os.getenv("NEST_ACCESS_TOKEN")

print("Environment variables loaded:")
print(f"NEST_PROJECT_ID: {NEST_PROJECT_ID}")
print(f"ACCESS_TOKEN: {ACCESS_TOKEN[:20]}..." if ACCESS_TOKEN else "None")

# API endpoints
NEST_API_ENDPOINT = 'https://smartdevicemanagement.googleapis.com/v1'

async def list_devices():
    """List all Nest devices."""
    url = f'{NEST_API_ENDPOINT}/enterprises/{NEST_PROJECT_ID}/devices'
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    print(f"\nRequest URL: {url}")
    print("Headers:", json.dumps(headers, indent=2))

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            print(f"\nResponse status: {response.status}")
            data = await response.json()
            print("\nResponse data:")
            print(json.dumps(data, indent=2))
            return data

async def get_device_traits(device_name):
    """Get traits for a specific device."""
    url = f'{NEST_API_ENDPOINT}/{device_name}'
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            print(f"\nDevice traits response status: {response.status}")
            data = await response.json()
            print("\nDevice traits:")
            print(json.dumps(data, indent=2))
            return data

async def main():
    """Main function to test Nest API access."""
    print("Testing Nest API access...")
    print(f"Using Project ID: {NEST_PROJECT_ID}")
    print(f"Access Token from env: {ACCESS_TOKEN}")
    
    try:
        # List all devices
        devices = await list_devices()
        
        # If we got devices, get details for the first one
        if 'devices' in devices and devices['devices']:
            first_device = devices['devices'][0]
            print(f"\nGetting details for device: {first_device['name']}")
            await get_device_traits(first_device['name'])
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    asyncio.run(main())
