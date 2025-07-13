#!/usr/bin/env python3
"""
Script to get Nest API access token using OAuth2 flow.
Run this script and follow the instructions to get your access token.
"""
import asyncio
import json
import os
import webbrowser
from aiohttp import web
from google_auth_oauthlib.flow import InstalledAppFlow

# Load client configuration from the downloaded JSON file
client_secrets_file = os.getenv("GOOGLE_CLIENT_SECRETS_FILE", "client_secret.json")
try:
    with open(client_secrets_file) as f:
        CLIENT_CONFIG = json.load(f)
except FileNotFoundError:
    print(f"Error: Could not find {client_secrets_file}")
    print("Please download your OAuth 2.0 client configuration from the Google Cloud Console")
    print("and save it in the current directory.")
    exit(1)

# OAuth 2.0 scopes for the SDM API
SCOPES = [
    'https://www.googleapis.com/auth/sdm.service',
    'https://www.googleapis.com/auth/pubsub'
]

async def callback_handler(request):
    """Handle the OAuth 2.0 callback."""
    try:
        # Get authorization code from URL parameters
        code = request.query.get('code')
        if code:
            # Exchange code for token
            flow = request.app['flow']
            token = flow.fetch_token(
                code=code,
                authorization_response=str(request.url)
            )
            request.app['token'] = token
            request.app['done'].set()
            return web.Response(text="Authorization successful! You can close this window.")
        return web.Response(text="Authorization failed: No code received")
    except Exception as e:
        print(f"Error in callback: {e}")
        return web.Response(text=f"Authorization failed: {str(e)}")

async def main():
    """Run the OAuth 2.0 flow and get access token."""
    app = web.Application()
    app['token'] = {}
    app['done'] = asyncio.Event()
    
    flow = InstalledAppFlow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri='http://localhost:8081/'
    )
    app['flow'] = flow
    
    app.router.add_get('/', callback_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8081)
    await site.start()
    
    print("Local server started on http://localhost:8081/")

    auth_url, _ = flow.authorization_url(
        prompt='consent'
    )
    print("\nPlease visit this URL to authorize this application:", auth_url)
    webbrowser.open(auth_url)

    # Wait for the callback to complete
    await app['done'].wait()
    
    # Get the token
    token = app['token']
    
    # Stop the web server
    await runner.cleanup()
    
    print("\nYour access token:")
    print(token['access_token'])
    print("\nAdd this to your .env file as NEST_ACCESS_TOKEN")
    
    # Save token to file
    with open('nest_token.json', 'w') as f:
        json.dump(token, f)
    print("\nFull token info saved to nest_token.json")
    
    return token

# Remove the old new_event_loop_for_token function as it's no longer needed

if __name__ == '__main__':
    asyncio.run(main())
