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
from typing import Set
from src.utils.logging import logger, setup_logger
from src.config.settings import (
    NEST_CLIENT_ID, NEST_CLIENT_SECRET, NEST_REFRESH_TOKEN,
    NEST_PROJECT_ID, GCP_PROJECT_ID, PUBSUB_SUBSCRIPTION_ID,
    validate_config
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
        task.result()
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Background task failed: {e}")
    finally:
        background_tasks.discard(task)

def create_background_task(coro) -> asyncio.Task:
    """Create and track a background task."""
    task = asyncio.create_task(coro)
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
        
        mqtt_client = MQTTClient()
        
        pubsub_client = PubSubClient(
            project_id=GCP_PROJECT_ID,
            subscription_id=PUBSUB_SUBSCRIPTION_ID,
            token_manager=token_manager
        )
        
        nest_api = NestAPI(
            project_id=NEST_PROJECT_ID,
            token_manager=token_manager
        )
        
        # Create background tasks
        tasks = [
            create_background_task(fetch_nest_periodically(nest_api)),
            create_background_task(mqtt_client.run_forever()),
            create_background_task(pubsub_client.start_listening())
        ]
        
        # Handle graceful shutdown
        loop = asyncio.get_running_loop()
        
        def handle_shutdown(sig: signal.Signals) -> None:
            logger.info(f"Received shutdown signal: {sig.name}")
            for task in background_tasks:
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
            await asyncio.gather(
                mqtt_client.stop(),
                pubsub_client.cleanup(),
                nest_api.close(),
                db.cleanup(),
                return_exceptions=True
            )
            
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
