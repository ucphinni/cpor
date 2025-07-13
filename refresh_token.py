#!/usr/bin/env python3
"""
Script to refresh Nest API access token using the refresh token.
This is a standalone utility that can be run independently or scheduled.
"""
import os
import json
import asyncio
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from dotenv import load_dotenv

async def refresh_access_token():
    """Refresh the access token using the refresh token."""
    # Load environment variables
    load_dotenv()
    
    # Get required credentials
    client_id = os.getenv('NEST_CLIENT_ID')
    client_secret = os.getenv('NEST_CLIENT_SECRET')
    refresh_token = os.getenv('NEST_REFRESH_TOKEN')
    
    if not all([client_id, client_secret, refresh_token]):
        print("ERROR: Missing required environment variables:")
        print("Required: NEST_CLIENT_ID, NEST_CLIENT_SECRET, NEST_REFRESH_TOKEN")
        return None
    
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Refreshing access token...")
        
        # Create credentials object
        creds = Credentials.from_authorized_user_info({
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token,
            'token_uri': 'https://oauth2.googleapis.com/token',
            'scopes': [
                'https://www.googleapis.com/auth/sdm.service',
                'https://www.googleapis.com/auth/pubsub'
            ]
        })

        # Refresh the token
        creds.refresh(Request())
        
        # Get the new access token
        new_access_token = creds.token
        expires_at = datetime.now() + timedelta(seconds=3600)  # 1 hour from now
        
        print(f"New access token: {new_access_token}")
        print(f"Token expires at: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Update the .env file with the new access token
        await update_env_file(new_access_token)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Access token has been refreshed and saved to .env file")
        return new_access_token
        
    except Exception as e:
        print(f"ERROR: Failed to refresh token: {e}")
        return None

async def update_env_file(new_token: str):
    """Update the .env file with the new access token."""
    try:
        # Read current file
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                lines = f.readlines()
        else:
            lines = []
        
        # Update or add the token line
        token_line_updated = False
        new_lines = []
        for line in lines:
            if line.startswith('NEST_ACCESS_TOKEN='):
                new_lines.append(f'NEST_ACCESS_TOKEN={new_token}\n')
                token_line_updated = True
            else:
                new_lines.append(line)
        
        # If we didn't find an existing line, add it
        if not token_line_updated:
            new_lines.append(f'NEST_ACCESS_TOKEN={new_token}\n')
        
        # Write back to file
        with open('.env', 'w') as f:
            f.writelines(new_lines)
            
        print("Updated .env file with new token")
        
    except Exception as e:
        print(f"WARNING: Could not update .env file: {e}")

if __name__ == '__main__':
    asyncio.run(refresh_access_token())
