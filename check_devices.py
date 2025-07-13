#!/usr/bin/env python3
"""
Check Nest Device Access project status and guide device linking.
"""
import os
import json
import aiohttp
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

NEST_PROJECT_ID = os.getenv("NEST_PROJECT_ID")
ACCESS_TOKEN = os.getenv("NEST_ACCESS_TOKEN")

async def check_device_access_status():
    """Check the current status of your Device Access project."""
    print("🔍 Checking Device Access Project Status...")
    print(f"Project ID: {NEST_PROJECT_ID}")
    print(f"Project Name: nest-therm-controller")
    print()
    
    # Check devices
    devices_url = f'https://smartdevicemanagement.googleapis.com/v1/enterprises/{NEST_PROJECT_ID}/devices'
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(devices_url, headers=headers) as response:
            print(f"API Response Status: {response.status}")
            data = await response.json()
            
            if response.status == 200:
                if 'devices' in data and data['devices']:
                    print(f"✅ Found {len(data['devices'])} device(s):")
                    for i, device in enumerate(data['devices'], 1):
                        print(f"  {i}. {device.get('displayName', 'Unknown')} ({device.get('type', 'Unknown Type')})")
                        print(f"     Device ID: {device['name']}")
                else:
                    print("❌ No devices found in your Device Access project")
                    print()
                    print("📋 To link your Nest thermostat:")
                    print("1. The thermostat must be on the SAME Google account used for OAuth")
                    print("2. Go to: https://console.nest.google.com/device-access/")
                    print("3. Click on your project: nest-therm-controller")
                    print("4. Look for device management or account linking options")
                    print("5. Ensure your Nest account is properly linked")
                    print()
                    print("🔗 Alternative method:")
                    print("1. Visit: https://nest.google.com/")
                    print("2. Sign in with the SAME Google account")
                    print("3. Ensure your thermostat is visible in the Nest app")
                    print("4. Then return to Device Access Console")
            else:
                print(f"❌ API Error: {data}")
                
        # Check structures (homes)
        structures_url = f'https://smartdevicemanagement.googleapis.com/v1/enterprises/{NEST_PROJECT_ID}/structures'
        async with session.get(structures_url, headers=headers) as response:
            print(f"\n🏠 Structures API Response Status: {response.status}")
            structures_data = await response.json()
            
            if response.status == 200:
                if 'structures' in structures_data and structures_data['structures']:
                    print(f"✅ Found {len(structures_data['structures'])} structure(s):")
                    for i, structure in enumerate(structures_data['structures'], 1):
                        print(f"  {i}. {structure.get('displayName', 'Home')} - {structure['name']}")
                else:
                    print("❌ No structures (homes) found")
                    print("This suggests your Nest account isn't linked to the Device Access project")
            else:
                print(f"❌ Structures API Error: {structures_data}")

def show_troubleshooting_guide():
    """Show troubleshooting steps for device linking."""
    print("\n" + "="*60)
    print("🛠️  TROUBLESHOOTING GUIDE")
    print("="*60)
    print()
    print("If you don't see your thermostat, check these:")
    print()
    print("1. 📧 SAME GOOGLE ACCOUNT:")
    print("   - OAuth was done with: ucphinni@gmail.com")
    print("   - Your Nest thermostat must be on the SAME account")
    print()
    print("2. 🏠 NEST APP VERIFICATION:")
    print("   - Go to: https://home.nest.google.com/")
    print("   - Sign in with ucphinni@gmail.com")
    print("   - Verify your thermostat appears there")
    print()
    print("3. 🔗 DEVICE ACCESS LINKING:")
    print("   - Go to: https://console.nest.google.com/device-access/")
    print("   - Click: nest-therm-controller project")
    print("   - Look for 'Account Linking' or 'Manage Devices'")
    print()
    print("4. 🔄 RE-AUTHORIZATION:")
    print("   - You may need to re-run the OAuth flow")
    print("   - This ensures all permissions are properly granted")
    print()
    print("5. ⏱️  WAIT TIME:")
    print("   - Device linking can take up to 15 minutes to propagate")
    print()

async def main():
    """Main function."""
    await check_device_access_status()
    show_troubleshooting_guide()

if __name__ == '__main__':
    asyncio.run(main())
