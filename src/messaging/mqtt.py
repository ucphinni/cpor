"""MQTT client implementation."""
from typing import Optional
import asyncio
from gmqtt import Client as GMQTTClient  # type: ignore
from ..utils.logging import logger
from ..utils.retry import with_retry
from ..config.settings import (
    MQTT_BROKER, MQTT_PORT, MQTT_USER, MQTT_PASSWORD,
    MQTT_USE_SSL, MQTT_TOPIC
)

class MQTTHandler:
    """MQTT connection handler."""
    def __init__(
        self,
        broker: str,
        port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_ssl: bool = False,
        topic: str = "#"
    ):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.topic = topic
        self.client = GMQTTClient("mqtt_handler")
        
        if username and password:
            self.client.set_auth_credentials(username, password)
            
    @with_retry(max_retries=3, exceptions=(Exception,))
    async def connect(self) -> None:
        """Connect to MQTT broker."""
        try:
            await self.client.connect(
                self.broker,
                port=self.port,
                ssl=self.use_ssl
            )
            logger.info(f"[MQTT] Connected to {self.broker}:{self.port}")
        except Exception as e:
            logger.error(f"[MQTT] Connection error: {e}")
            raise
            
    async def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        try:
            await self.client.disconnect()
            logger.info("[MQTT] Disconnected from broker")
        except Exception as e:
            logger.error(f"[MQTT] Disconnect error: {e}")

class MQTTClient:
    """MQTT client wrapper with retry logic."""
    def __init__(
        self,
        broker: str = MQTT_BROKER,
        port: int = MQTT_PORT,
        username: Optional[str] = MQTT_USER,
        password: Optional[str] = MQTT_PASSWORD,
        use_ssl: bool = MQTT_USE_SSL,
        topic: str = MQTT_TOPIC
    ):
        """Initialize MQTT client."""
        self._handler = MQTTHandler(
            broker=broker,
            port=port,
            username=username,
            password=password,
            use_ssl=use_ssl,
            topic=topic
        )
        self._stopping = False

    @with_retry(max_retries=3, exceptions=(Exception,))
    async def connect(self) -> None:
        """Connect to the MQTT broker."""
        await self._handler.connect()
            
    async def run_forever(self) -> None:
        """Keep the MQTT connection alive."""
        # Connect first with retry
        await self.connect()
        try:
            while not self._stopping:
                await asyncio.sleep(10)  # Keep alive heartbeat
        except asyncio.CancelledError:
            pass

    async def stop(self) -> None:
        """Stop the MQTT client."""
        self._stopping = True
        await self._handler.disconnect()
