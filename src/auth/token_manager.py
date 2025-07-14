"""OAuth2 token management for Google services."""
import asyncio
from datetime import datetime, timedelta
from typing import Optional
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from ..utils.logging import logger
from ..utils.retry import with_retry

class TokenManager:
    """Manages Google OAuth2 token refresh automatically."""
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token: Optional[str] = None
        self.expires_at: Optional[datetime] = None
        self._refresh_lock = asyncio.Lock()
        
    def _load_from_env(self) -> None:
        """Load current access token from environment."""
        self.access_token = os.getenv('NEST_ACCESS_TOKEN')
        
    @with_retry(max_retries=3, exceptions=(Exception,))
    async def get_valid_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        async with self._refresh_lock:
            if not self.access_token:
                self._load_from_env()
                
            if not self.access_token or self._is_token_expired():
                logger.info("[TokenManager] Token is missing or expired, refreshing...")
                await self._refresh_token()
                
            if not self.access_token:
                raise RuntimeError("Failed to obtain a valid access token")
            return self.access_token
        
    def _is_token_expired(self) -> bool:
        """Check if the current token is expired or will expire soon."""
        if not self.expires_at:
            return True
        buffer_time = timedelta(minutes=10)
        return datetime.now() >= (self.expires_at - buffer_time)
        
    async def _refresh_token(self) -> None:
        """Refresh the access token using the refresh token."""
        try:
            logger.info("[TokenManager] Refreshing access token...")
            
            creds = Credentials.from_authorized_user_info({
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token,
                'token_uri': 'https://oauth2.googleapis.com/token',
                'scopes': [
                    'https://www.googleapis.com/auth/sdm.service',
                    'https://www.googleapis.com/auth/pubsub'
                ]
            })
            
            # Use run_in_executor for the blocking refresh operation
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, creds.refresh, Request())
            
            self.access_token = creds.token
            self.expires_at = datetime.now() + timedelta(seconds=3600)
            
            await self._update_env_file()
            
            logger.info("[TokenManager] Access token refreshed successfully")
            
        except Exception as e:
            logger.error(f"[TokenManager] Failed to refresh token: {e}")
            self.access_token = None
            self.expires_at = None
            raise
            
    async def _update_env_file(self) -> None:
        """Update the .env file with the new access token asynchronously."""
        if not self.access_token:
            return
            
        def _update_env_sync():
            try:
                if os.path.exists('.env'):
                    with open('.env', 'r') as f:
                        lines = f.readlines()
                else:
                    lines = []
                
                token_updated = False
                new_lines = []
                
                for line in lines:
                    if line.startswith('NEST_ACCESS_TOKEN='):
                        new_lines.append(f'NEST_ACCESS_TOKEN={self.access_token}\n')
                        token_updated = True
                    else:
                        new_lines.append(line)
                
                if not token_updated:
                    new_lines.append(f'NEST_ACCESS_TOKEN={self.access_token}\n')
                
                with open('.env', 'w') as f:
                    f.writelines(new_lines)
                    
                logger.debug("[TokenManager] Updated .env file with new token")
                
            except Exception as e:
                logger.warning(f"[TokenManager] Could not update .env file: {e}")
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _update_env_sync)
