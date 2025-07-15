#!/usr/bin/env python3
"""
MVP3: Modular async Nest controller
- Uses modular architecture for better maintainability
- Async SQLAlchemy for database operations
- MQTT client with retry logic
- Pub/Sub client with gRPC streaming and retry
- Nest API with token refresh and retry
- Proper error handling and cleanup
"""

import asyncio
import signal
import json
from typing import Set, Optional
from src.utils.logging import logger, setup_logger
from src.config.settings import (
    NEST_CLIENT_ID, NEST_CLIENT_SECRET, NEST_REFRESH_TOKEN,
    NEST_PROJECT_ID, GCP_PROJECT_ID, PUBSUB_SUBSCRIPTION_ID,
    validate_config, ZIGBEE2MQTT_TOPICS
)
from src.auth.token_manager import TokenManager
from src.database.operations import Database
from src.messaging.mqtt import MQTTClient
from src.messaging.pubsub import PubSubClient
from src.nest.api import NestAPI

# Set up logging
logger = setup_logger("mvp3")

# Track tasks for graceful shutdown
background_tasks: Set[asyncio.Task] = set()

def handle_task_result(task: asyncio.Task) -> None:
    """Handle background task completion."""
    try:
        if not task.cancelled():
            result = task.result()
            logger.debug(f"Background task completed: {task.get_name()}")
    except asyncio.CancelledError:
        logger.info(f"Background task cancelled: {task.get_name()}")
    except Exception as e:
        logger.error(f"Background task failed ({task.get_name()}): {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        background_tasks.discard(task)

def create_background_task(coro, name: Optional[str] = None) -> asyncio.Task:
    """Create and track a background task."""
    task = asyncio.create_task(coro, name=name)
    background_tasks.add(task)
    task.add_done_callback(handle_task_result)
    return task

async def fetch_nest_periodically(nest_api: NestAPI) -> None:
    """Periodically fetch Nest device data."""
    while True:
        try:
            devices = await nest_api.list_devices()
            for device in devices.get("devices", []):
                device_id = device["name"].split("/")[-1]
                device_type = device.get("type", "")
                if "THERMOSTAT" in device_type:
                    logger.info(f"Thermostat: {device_id} {device_type}")
                    try:
                        temps = await nest_api.get_temperature(device_id)
                        logger.info(f"Temperatures: {temps}")
                    except Exception as e:
                        logger.error(f"Error getting temperature for {device_id}: {e}")
        except Exception as e:
            logger.error(f"Error fetching Nest devices: {e}")
        await asyncio.sleep(300)  # 5 minutes

class ZigbeeDiscovery:
    def __init__(self, mqtt_client, topics):
        self.mqtt_client = mqtt_client
        self.topics = topics
        self.devices = {}

    async def start(self):
        # Subscribe to bridge/devices for each top-level topic
        for base in self.topics:
            await self.mqtt_client.subscribe(f"{base}/bridge/devices")
            await self.mqtt_client.subscribe(f"{base}/#")
        logger.info(f"[Zigbee] Subscribed to: {[f'{base}/#' for base in self.topics]} and bridge/devices")

    async def handle_message(self, topic, payload):
        # Device list update
        for base in self.topics:
            if topic == f"{base}/bridge/devices":
                try:
                    devices = json.loads(payload)
                    self.devices = {d['friendly_name']: d for d in devices}
                    logger.info(f"[Zigbee] Discovered devices: {list(self.devices.keys())}")
                except Exception as e:
                    logger.error(f"[Zigbee] Failed to parse device list: {e}")
                return
            # Device payloads
            if topic.startswith(f"{base}/") and not topic.startswith(f"{base}/bridge/"):
                device_name = topic[len(f"{base}/"):].split("/")[0]
                logger.info(f"[Zigbee] Device update: {device_name} | Topic: {topic} | Payload: {payload}")
                # Optionally update state, database, etc.

async def run() -> None:
    """Main application entry point."""
    logger.info("Starting MVP3 Nest controller...")
    
    try:
        # Validate configuration
        validate_config()
        
        # Initialize token manager
        token_manager = TokenManager(
            NEST_CLIENT_ID,
            NEST_CLIENT_SECRET,
            NEST_REFRESH_TOKEN
        )
        
        # Initialize components
        db = Database()
        await db.init_db()
        
        # Add a default house if none exists
        await db.add_house("My House", "Primary residence")
        await db.list_houses()
        
        # Initialize MQTT client
        mqtt_client = MQTTClient()
        zigbee_discovery = ZigbeeDiscovery(mqtt_client, ZIGBEE2MQTT_TOPICS)
        await zigbee_discovery.start()

        # Patch MQTT client to call zigbee discovery handler
        def zigbee_message_handler(topic, payload, client):
            asyncio.create_task(zigbee_discovery.handle_message(topic, payload.decode('utf-8')))
        mqtt_client.set_change_callback(zigbee_message_handler)
        
        pubsub_client = PubSubClient(
            project_id=GCP_PROJECT_ID,
            subscription_id=PUBSUB_SUBSCRIPTION_ID,
            token_manager=token_manager
        )
        
        nest_api = NestAPI(
            project_id=NEST_PROJECT_ID,
            token_manager=token_manager
        )
        
        # Create background tasks (with MQTT and Zigbee discovery)
        tasks = [
            create_background_task(fetch_nest_periodically(nest_api), "nest_fetcher"),
            create_background_task(mqtt_client.run_forever(), "mqtt_client"),
            create_background_task(pubsub_client.start_listening(), "pubsub_listener")
        ]
        
        logger.info("Started tasks: Nest API fetcher, MQTT client, and Pub/Sub listener")
        
        # Handle graceful shutdown
        loop = asyncio.get_running_loop()
        
        def handle_shutdown(sig: signal.Signals) -> None:
            logger.info(f"Received shutdown signal: {sig.name}")
            for task in tasks:  # Fixed: use 'tasks' instead of 'background_tasks'
                task.cancel()
        
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda s=sig: handle_shutdown(s))
            
        # Wait for tasks to complete or be cancelled
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except asyncio.CancelledError:
            pass
        finally:
            # Cleanup
            logger.info("Cleaning up resources...")
            cleanup_tasks = [
                pubsub_client.cleanup(),
                nest_api.close(),
                db.cleanup(),
            ]
            
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Shutting down due to keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
