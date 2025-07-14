"""Google Cloud Pub/Sub client implementation."""
import asyncio
import json
from typing import Optional, Callable, Any
from google.cloud import pubsub_v1
import google.auth.credentials
import google.oauth2.credentials
from ..utils.logging import logger
from ..utils.retry import with_retry
from ..auth.token_manager import TokenManager
from ..config.settings import GCP_PROJECT_ID, PUBSUB_SUBSCRIPTION_ID

class PubSubClient:
    """Google Cloud Pub/Sub client for real-time Nest events using gRPC streaming pull."""
    
    def __init__(
        self,
        project_id: str = GCP_PROJECT_ID,
        subscription_id: str = PUBSUB_SUBSCRIPTION_ID,
        token_manager: Optional[TokenManager] = None
    ):
        self.project_id = project_id
        self.subscription_id = subscription_id
        self.token_manager = token_manager
        self._running = False
        self._subscriber = None
        self._streaming_pull_future = None
        
    @with_retry(max_retries=3, exceptions=(Exception,))
    async def _get_credentials(self) -> google.auth.credentials.Credentials:
        """Get Google Auth credentials."""
        if not self.token_manager:
            raise ValueError("Token manager not configured")
        token = await self.token_manager.get_valid_token()
        return google.oauth2.credentials.Credentials(
            token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=self.token_manager.client_id,
            client_secret=self.token_manager.client_secret,
            refresh_token=self.token_manager.refresh_token,
            scopes=['https://www.googleapis.com/auth/pubsub']
        )

    async def start_listening(self, callback=None):
        """Start listening for Pub/Sub messages using gRPC streaming pull."""
        self._running = True
        logger.info("[PubSub] Starting to listen for Nest events using gRPC...")
        
        try:
            # Create subscriber client with automatic token refresh
            credentials = await self._get_credentials()
            
            self._subscriber = pubsub_v1.SubscriberClient(
                credentials=credentials
            )
            
            # Ensure subscription_id doesn't already contain the full path
            clean_subscription_id = self.subscription_id.split('/')[-1] if '/' in self.subscription_id else self.subscription_id
            
            subscription_path = self._subscriber.subscription_path(
                self.project_id, 
                clean_subscription_id
            )
            logger.info(f"[PubSub] Using subscription path: {subscription_path}")

            # Define message callback - must be synchronous for Google Cloud PubSub
            def message_callback(message):
                try:
                    if callback:
                        # If callback is async, we need to run it in an event loop
                        if asyncio.iscoroutinefunction(callback):
                            asyncio.create_task(self._handle_async_callback(callback, message))
                        else:
                            callback(message)
                            message.ack()
                    else:
                        # Handle sync version of default handler
                        self._default_message_handler_sync(message)
                        message.ack()
                except Exception as e:
                    logger.error(f"[PubSub] Error processing message: {e}")
                    message.nack()

            # Start streaming pull
            flow_control = pubsub_v1.types.FlowControl(
                max_messages=100,  # Number of messages to buffer
                max_bytes=10 * 1024 * 1024  # 10MB
            )

            self._streaming_pull_future = self._subscriber.subscribe(
                subscription_path,
                callback=message_callback,
                flow_control=flow_control
            )

            # Wait for the streaming pull to complete or be cancelled
            await self._streaming_pull_future.result()

        except Exception as e:
            logger.error(f"[PubSub] Error in gRPC streaming pull: {e}")
            if self._running:
                # If the error is related to invalid resource name, stop retrying
                if "Invalid resource name given" in str(e):
                    logger.error("[PubSub] Invalid subscription configuration. Please check your subscription ID.")
                    self._running = False
                else:
                    # For other errors, attempt to reconnect after a delay
                    await asyncio.sleep(5)
                    asyncio.create_task(self.start_listening(callback))

    async def _handle_async_callback(self, callback, message):
        """Handle async callback in a proper async context."""
        try:
            await callback(message)
            message.ack()
        except Exception as e:
            logger.error(f"[PubSub] Error in async callback: {e}")
            message.nack()

    def _default_message_handler_sync(self, message):
        """Synchronous version of the default message handler."""
        try:
            # Parse message data
            data = json.loads(message.data.decode("utf-8"))
            logger.info(f"[PubSub] Nest event: {data}")
            
            # Extract device info
            if "resourceUpdate" in data:
                resource = data["resourceUpdate"]
                device_name = resource.get("name", "Unknown")
                traits = resource.get("traits", {})
                logger.info(f"[PubSub] Device {device_name} updated: {traits}")
                
        except Exception as e:
            logger.error(f"[PubSub] Failed to process message: {e}")
            raise

    async def _default_message_handler(self, message):
        """Default handler for Pub/Sub messages."""
        return self._default_message_handler_sync(message)

    def stop(self):
        """Stop listening for messages."""
        self._running = False
        if self._streaming_pull_future:
            self._streaming_pull_future.cancel()
        if self._subscriber:
            self._subscriber.close()
        logger.info("[PubSub] Stopping gRPC message listener...")
            
    async def cleanup(self) -> None:
        """Clean up Pub/Sub resources."""
        self.stop()
