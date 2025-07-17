"""MQTT client implementation."""
from typing import List, Optional, Callable, Dict, Any, Union, Awaitable
import asyncio
import json
import traceback
from gmqtt import Client as GMQTTClient  # type: ignore
from gmqtt.mqtt.constants import MQTTv311
from ..utils.logging import logger
from ..utils.retry import with_retry
from ..config.settings import BROKER_CONFIGS
from ..utils.zigbee import extract_zigbee_friendly_name, register_broker_topics

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
        self.client: GMQTTClient = GMQTTClient(client_id=self.username or "cpor-client")
        if self.username and self.password:
            self.client.set_auth_credentials(self.username, self.password)
        logger.info(f"[MQTT] Created MQTT client: {type(self.client)}")

    @with_retry(max_retries=3, exceptions=(Exception,))
    async def connect(self) -> None:
        """Connect to the MQTT broker."""
        logger.info(f"[MQTT] Set auth credentials for user: {self.username}")
        await self.client.connect(
            self.broker,
            port=self.port,
            ssl=self.use_ssl,
            version=MQTTv311
        )
        logger.info(f"[MQTT] Connected to {self.broker}:{self.port}")

    async def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        try:
            await self.client.disconnect()
            logger.info(f"[MQTT] Disconnected from {self.broker}:{self.port}")
        except Exception as e:
            logger.error(f"[MQTT] Error during disconnect: {e}")

class MQTTClient:
    """
    MQTT client wrapper for Zigbee2MQTT-focused async message handling.
    
    Features:
    - Dedicated Zigbee2MQTT message handler
    - All callbacks receive broker/client name, topic, decoded payload, and friendly_name
    - No generic change detection or last-value caching
    - Fully async event handlers
    """
    def __init__(
        self,
        broker: str,
        port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_ssl: bool = False,
        topic: str = "#",
        zigbee2mqtt_callback: Optional[Callable[[str, str, Any, Optional[str]], Awaitable[None]]] = None,
        zigbee2mqtt_topics: Optional[List[str]] = None,
        broker_id: Optional[str] = None,
        mqtt_version: int = 311,
    ):
        """Initialize Zigbee2MQTT-focused MQTT client."""
        self._handler = MQTTHandler(
            broker=broker,
            port=port,
            username=username,
            password=password,
            use_ssl=use_ssl,
            topic=topic
        )
        self._mqtt_version = mqtt_version
        self._stopping = False
        self._zigbee2mqtt_callback = zigbee2mqtt_callback
        self._handlers_setup = False
        self._broker_id = broker_id or broker
        self._zigbee2mqtt_topics = zigbee2mqtt_topics or []
        self._unsubscribed_topics = set()
        if self._zigbee2mqtt_topics:
            register_broker_topics(self._broker_id, self._zigbee2mqtt_topics)

    def _setup_handlers(self):
        """Set up MQTT client event handlers for Zigbee2MQTT."""
        if self._handlers_setup:
            return
        # Only on_message should be async; others must be sync
        def on_connect(client, flags, rc, properties):
            logger.info(f"[MQTT] on_connect called: rc={rc}, flags={flags}, properties={properties}")
            client.broker_id = self._broker_id
            # Only subscribe to +/+/availability on connect
            client.subscribe("+/+/availability", qos=1)
            logger.info("[MQTT] Subscribed to topic: +/+/availability")
        # Track device topic subscriptions to prevent duplicates
        self._subscribed_device_topics = set()
        async def on_message(client, topic, payload, qos, properties):
            logger.info(f"[MQTT] on_message called: topic={topic}, qos={qos}, properties={properties}")
            parts = topic.split("/")
            # Only handle availability messages from the +/+/availability subscription, not from device topic subscriptions
            if len(parts) == 3 and parts[2] == "availability" and parts[1] != 'bridge' and topic not in self._subscribed_device_topics:
                zigbee_base = parts[0]
                device_id = parts[1]
                state_str = str(payload).strip().lower()
                if "online" in state_str:
                    state = "online"
                elif "offline" in state_str:
                    state = "offline"
                else:
                    state = state_str
                device_topic = f"{zigbee_base}/{device_id}/#"
                if state == "online":
                    if device_topic not in self._subscribed_device_topics:
                        client.subscribe(device_topic, qos=1)
                        self._subscribed_device_topics.add(device_topic)
                        logger.info(f"[MQTT] Dynamically subscribed to device topic: {device_topic}")
                    else:
                        logger.debug(f"[MQTT] Already subscribed to device topic: {device_topic}")
                    return
                elif state == "offline":
                    if device_topic in self._subscribed_device_topics:
                        client.unsubscribe(device_topic)
                        self._subscribed_device_topics.remove(device_topic)
                        logger.info(f"[MQTT] Dynamically unsubscribed from device topic: {device_topic}")
                    else:
                        logger.debug(f"[MQTT] Already unsubscribed from device topic: {device_topic}")
                    return
            # ...existing message decoding and callback logic...
            try:
                broker_id = getattr(client, "broker_id", None)
                friendly_name = None
                if broker_id is not None:
                    friendly_name = extract_zigbee_friendly_name(topic, broker_id)
                logger.debug(f"[MQTT] Received message on {topic}: type={type(payload)}, value={payload}, friendly_name={friendly_name}, broker_id={broker_id}")
                decoded_payload = None
                if payload is None:
                    decoded_payload = {"event": "offline"}
                elif isinstance(payload, dict):
                    decoded_payload = payload
                elif isinstance(payload, bytes):
                    try:
                        message_str = payload.decode('utf-8')
                        try:
                            decoded_payload = json.loads(message_str)
                        except json.JSONDecodeError:
                            decoded_payload = message_str
                    except Exception as e:
                        logger.error(f"[MQTT] Error decoding bytes payload on {topic}: {e}", exc_info=True)
                        decoded_payload = str(payload)
                elif isinstance(payload, str):
                    try:
                        decoded_payload = json.loads(payload)
                    except json.JSONDecodeError:
                        decoded_payload = payload
                else:
                    decoded_payload = str(payload)
                if self._zigbee2mqtt_callback is not None:
                    try:
                        safe_broker_id = broker_id if broker_id is not None else ""
                        logger.info(f"[MQTT] Invoking zigbee2mqtt_callback for topic={topic}")
                        result = self._zigbee2mqtt_callback(safe_broker_id, topic, decoded_payload, friendly_name)
                        if asyncio.iscoroutine(result):
                            await result
                    except Exception as cb_exc:
                        logger.error(f"[MQTT] Zigbee2MQTT callback error on {topic}: {cb_exc}", exc_info=True)
            except Exception as e:
                logger.error(f"[MQTT] Unhandled error processing Zigbee2MQTT message on {topic}: {e}", exc_info=True)
            return 0
        def on_disconnect(client, packet, exc=None):
            logger.info(f"[MQTT] on_disconnect called: packet={packet}, exc={exc}")
            logger.warning("[MQTT] Disconnected from broker")
        def on_subscribe(client, mid, qos, properties):
            logger.info(f"[MQTT] on_subscribe called: mid={mid}, qos={qos}, properties={properties}")
            logger.info(f"[MQTT] Subscription confirmed with QoS {qos}")
        self._handler.client.on_connect = on_connect
        self._handler.client.on_message = on_message
        self._handler.client.on_disconnect = on_disconnect
        self._handler.client.on_subscribe = on_subscribe
        self._handlers_setup = True

    def set_zigbee2mqtt_callback(self, callback: Callable[[str, str, Any, Optional[str]], Awaitable[None]]) -> None:
        """
        Set or update the Zigbee2MQTT event callback.
        Callback signature: (broker/client name, topic, decoded payload, friendly_name)
        """
        self._zigbee2mqtt_callback = callback

    # Utility for wrapping sync grpc calls if needed
    @staticmethod
    async def run_sync_in_executor(func: Callable, *args, **kwargs) -> Any:
        """
        Run a sync function in an executor from async context.
        Use for grpc thermostat operations that must be sync.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)

    async def subscribe(self, topic: str, qos: int = 1) -> None:
        """Subscribe to an MQTT topic."""
        if not self._handler.client:
            logger.error("[MQTT] Cannot subscribe: client is not initialized")
            raise ValueError("MQTT client is not initialized")
        if not hasattr(self._handler.client, '_connection') or self._handler.client._connection is None:
            logger.info("[MQTT] Client not connected, connecting first...")
            await self.connect()
        try:
            self._handler.client.subscribe(topic, qos=qos)
            logger.info(f"[MQTT] Subscribed to topic: {topic}")
        except Exception as e:
            logger.error(f"[MQTT] Failed to subscribe to {topic}: {e}")
            raise

    async def publish(self, topic: str, payload: Any, qos: int = 1, retain: bool = False) -> None:
        """Publish a message to MQTT broker."""
        if not self._handler.client:
            logger.error("[MQTT] Cannot publish: client is not initialized")
            raise ValueError("MQTT client is not initialized")
        try:
            if isinstance(payload, (dict, list)):
                message = json.dumps(payload)
            else:
                message = str(payload)
            self._handler.client.publish(topic, message, qos=qos, retain=retain)
            logger.debug(f"[MQTT] Published to {topic}: {message}")
        except Exception as e:
            logger.error(f"[MQTT] Failed to publish to {topic}: {e}")

    @with_retry(max_retries=3, exceptions=(Exception,))
    async def connect(self) -> None:
        """Connect to the MQTT broker and subscribe to broker-specific topics."""
        self._setup_handlers()
        logger.info(f"[MQTT] Connecting to {self._handler.broker}:{self._handler.port} with protocol MQTTv{self._mqtt_version}...")
        await self._handler.client.connect(
            self._handler.broker,
            port=self._handler.port,
            ssl=self._handler.use_ssl,
            version=self._mqtt_version
        )
        logger.info(f"[MQTT] Connected to {self._handler.broker}:{self._handler.port}")
        # Subscribe only to '+/+/availability'
        self._handler.client.subscribe("+/+/availability", qos=1)
        logger.info("[MQTT] Subscribed to topic: +/+/availability")

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

    async def dynamic_subscribe(self, topic: str, qos: int = 1) -> None:
        """Dynamically subscribe to a new MQTT topic."""
        try:
            if not hasattr(self._handler.client, '_connection') or self._handler.client._connection is None:
                logger.info("[MQTT] Client not connected, connecting first...")
                await self.connect()
            self._handler.client.subscribe(topic, qos=qos)
            logger.info(f"[MQTT] Dynamically subscribed to topic: {topic}")
        except Exception as e:
            logger.error(f"[MQTT] Failed to dynamically subscribe to {topic}: {e}")
            raise

    async def dynamic_unsubscribe(self, topic: str) -> None:
        """Dynamically unsubscribe from an MQTT topic."""
        try:
            self._handler.client.unsubscribe(topic)
            logger.info(f"[MQTT] Dynamically unsubscribed from topic: {topic}")
        except Exception as e:
            logger.error(f"[MQTT] Failed to dynamically unsubscribe from {topic}: {e}")
            raise

    async def _handle_unsubscription(self, client, topic: str) -> None:
        """Handle unsubscription logic for specific topics."""
        if topic not in self._unsubscribed_topics:
            try:
                client.unsubscribe(topic)
                self._unsubscribed_topics.add(topic)
                logger.info(f"[MQTT] Unsubscribed from topic: {topic}")
            except Exception as e:
                logger.error(f"[MQTT] Failed to unsubscribe from {topic}: {e}")

class MultiMQTTClient:
    """
    Multi-broker MQTT client manager. Instantiates and manages multiple MQTTClient instances, each with broker-specific Zigbee2MQTT topics.
    """
    def __init__(self, zigbee2mqtt_callback: Optional[Callable[[str, str, Any, Optional[str]], Awaitable[None]]] = None):
        self.clients = []
        # Handle case where no brokers are configured
        if not BROKER_CONFIGS:
            logger.warning("[MQTT] No broker configurations found. MultiMQTTClient will have no active clients.")
            return
        for idx, cfg in enumerate(BROKER_CONFIGS):
            client = MQTTClient(
                broker=cfg["broker"],
                port=cfg["port"],
                username=cfg["user"],
                password=cfg["password"],
                use_ssl=cfg["use_ssl"],
                zigbee2mqtt_callback=zigbee2mqtt_callback,
                broker_id=cfg["broker"],
                mqtt_version=int(cfg.get("version", 311)),
            )
            self.clients.append(client)
            logger.info(f"[MQTT] Created client for broker: {cfg['broker']}:{cfg['port']}")

    async def connect_all(self) -> None:
        """Connect all clients to their respective brokers."""
        for client in self.clients:
            await client.connect()

    async def run_all_forever(self) -> None:
        """Run all MQTT clients forever."""
        if not self.clients:
            logger.warning("[MQTT] No clients to run. Waiting indefinitely...")
            try:
                while True:
                    await asyncio.sleep(60)
            except asyncio.CancelledError:
                logger.info("[MQTT] MultiMQTTClient cancelled")
            return
        async def run_single_client(client):
            try:
                await client.run_forever()
            except Exception as e:
                logger.error(f"[MQTT] Error in client {client._broker_id}: {e}")
                raise
        try:
            await asyncio.gather(*[run_single_client(client) for client in self.clients])
        except asyncio.CancelledError:
            logger.info("[MQTT] MultiMQTTClient cancelled")
            raise

    async def stop_all(self) -> None:
        """Stop all MQTT clients."""
        for client in self.clients:
            await client.stop()

    async def cleanup(self) -> None:
        """Clean up all MQTT clients."""
        await self.stop_all()

    async def publish_all(self, topic: str, payload: Any, qos: int = 1, retain: bool = False) -> None:
        """Publish a message to all brokers."""
        for client in self.clients:
            await client.publish(topic, payload, qos=qos, retain=retain)

    async def subscribe_all(self, topic: str, qos: int = 1) -> None:
        """Subscribe to a topic on all brokers."""
        for client in self.clients:
            await client.subscribe(topic, qos=qos)

__all__ = [
    "MQTTHandler",
    "MQTTClient",
    "MultiMQTTClient"
]
