"""MQTT client implementation."""
from typing import Optional, Callable, Dict, Any
import asyncio
import json
from gmqtt import Client as GMQTTClient  # type: ignore
from gmqtt.mqtt.constants import MQTTv311
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
    """
    MQTT client wrapper with async change detection and last value caching.
    
    Features:
    - Maintains last known values for all topics
    - Detects changes and notifies controller
    - Async message handling
    - Automatic reconnection with retry logic
    """
    def __init__(
        self,
        broker: str = MQTT_BROKER,
        port: int = MQTT_PORT,
        username: Optional[str] = MQTT_USER,
        password: Optional[str] = MQTT_PASSWORD,
        use_ssl: bool = MQTT_USE_SSL,
        topic: str = MQTT_TOPIC,
        change_callback: Optional[Callable[[str, Any, Any], None]] = None
    ):
        """Initialize MQTT client with change detection."""
        self._handler = MQTTHandler(
            broker=broker,
            port=port,
            username=username,
            password=password,
            use_ssl=use_ssl,
            topic=topic
        )
        self._stopping = False
        self._change_callback = change_callback
        
        # Last value cache for change detection
        self._last_values: Dict[str, Any] = {}
        
        # Set up MQTT event handlers
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up MQTT client event handlers."""
        @self._handler.client.on_connect()
        def on_connect(client, flags, rc, properties):
            logger.info(f"[MQTT] Connected with result code {rc}")
            # Subscribe to topics after connection
            if self._handler.topic:
                client.subscribe(self._handler.topic, qos=1)
                logger.info(f"[MQTT] Subscribed to topic: {self._handler.topic}")

        @self._handler.client.on_message()
        def on_message(client, topic, payload, qos, properties):
            """Handle incoming MQTT messages with change detection."""
            try:
                # Decode message
                message_str = payload.decode('utf-8')
                
                # Try to parse as JSON, fallback to string
                try:
                    current_value = json.loads(message_str)
                except json.JSONDecodeError:
                    current_value = message_str
                
                # Check if value changed
                last_value = self._last_values.get(topic)
                
                if last_value != current_value:
                    # Value changed - update cache and notify
                    self._last_values[topic] = current_value
                    
                    logger.info(f"[MQTT] Change detected on {topic}: {last_value} -> {current_value}")
                    
                    # Notify controller of change (async callback)
                    if self._change_callback:
                        # Schedule async callback if it's a coroutine
                        if asyncio.iscoroutinefunction(self._change_callback):
                            asyncio.create_task(
                                self._change_callback(topic, last_value, current_value)
                            )
                        else:
                            # Call sync callback directly
                            self._change_callback(topic, last_value, current_value)
                else:
                    logger.debug(f"[MQTT] No change on {topic}: {current_value}")
                    
            except Exception as e:
                logger.error(f"[MQTT] Error processing message on {topic}: {e}")

        @self._handler.client.on_disconnect()
        def on_disconnect(client, packet, exc=None):
            logger.warning("[MQTT] Disconnected from broker")

        @self._handler.client.on_subscribe()
        def on_subscribe(client, mid, qos, properties):
            logger.info(f"[MQTT] Subscription confirmed with QoS {qos}")

    def set_change_callback(self, callback: Callable[[str, Any, Any], None]):
        """Set or update the change detection callback."""
        self._change_callback = callback

    def get_last_value(self, topic: str) -> Optional[Any]:
        """Get the last known value for a topic."""
        return self._last_values.get(topic)

    def get_all_values(self) -> Dict[str, Any]:
        """Get all last known values."""
        return self._last_values.copy()

    async def publish(self, topic: str, payload: Any, qos: int = 1, retain: bool = False) -> None:
        """Publish a message to MQTT broker."""
        try:
            # Convert payload to string if needed
            if isinstance(payload, (dict, list)):
                message = json.dumps(payload)
            else:
                message = str(payload)
            
            self._handler.client.publish(topic, message, qos=qos, retain=retain)
            logger.debug(f"[MQTT] Published to {topic}: {message}")
            
            # Update our own cache for published messages
            try:
                parsed_payload = json.loads(message) if isinstance(payload, (dict, list)) else payload
                self._last_values[topic] = parsed_payload
            except:
                self._last_values[topic] = payload
                
        except Exception as e:
            logger.error(f"[MQTT] Failed to publish to {topic}: {e}")
            raise

    @with_retry(max_retries=3, exceptions=(Exception,))
    async def connect(self) -> None:
        """Connect to the MQTT broker."""
        await self._handler.connect()
            
    async def run_forever(self) -> None:
        """Keep the MQTT connection alive and handle messages."""
        # Connect first with retry
        await self.connect()
        try:
            while not self._stopping:
                await asyncio.sleep(10)  # Keep alive heartbeat
        except asyncio.CancelledError:
            logger.info("[MQTT] MQTT client cancelled")
        except Exception as e:
            logger.error(f"[MQTT] Error in run_forever: {e}")
            raise

    async def stop(self) -> None:
        """Stop the MQTT client."""
        self._stopping = True
        await self._handler.disconnect()
        logger.info("[MQTT] MQTT client stopped")

    async def cleanup(self) -> None:
        """Clean up MQTT resources."""
        await self.stop()
