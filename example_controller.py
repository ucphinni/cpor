"""Example controller showing async MQTT change detection integration."""
import asyncio
import json
from typing import Any, Dict
from src.messaging.mqtt import MQTTClient
from src.messaging.pubsub import PubSubClient
from src.database.operations import Database
from src.auth.token_manager import TokenManager
from src.utils.logging import logger

class SmartHomeController:
    """
    Main controller that coordinates between Nest events and MQTT device updates.
    
    Architecture:
    - Nest events (sync callback) drive the main logic
    - MQTT changes (async) update device states  
    - Controller orchestrates async operations
    """
    
    def __init__(self):
        self.token_manager = TokenManager()
        self.database = Database()
        self.pubsub_client = PubSubClient(token_manager=self.token_manager)
        
        # MQTT client with change detection callback
        self.mqtt_client = MQTTClient(
            topic="home/devices/+/state",  # Subscribe to all device states
            change_callback=self.on_mqtt_change  # Async change handler
        )
        
        self._running = False
        
    async def on_mqtt_change(self, topic: str, old_value: Any, new_value: Any):
        """
        Handle MQTT device state changes asynchronously.
        This gets called whenever any MQTT device state changes.
        """
        try:
            logger.info(f"[Controller] MQTT change detected: {topic}")
            logger.info(f"[Controller] {old_value} -> {new_value}")
            
            # Extract device ID from topic (e.g., "home/devices/thermostat/state")
            topic_parts = topic.split('/')
            if len(topic_parts) >= 3:
                device_id = topic_parts[2]
                
                # Update database with new device state (async)
                await self.database.update_device_state(device_id, new_value)
                
                # Check if this change should trigger any automation rules
                await self.check_automation_rules(device_id, old_value, new_value)
                
        except Exception as e:
            logger.error(f"[Controller] Error handling MQTT change: {e}")
    
    async def on_nest_event(self, message):
        """
        Handle Nest device events from Pub/Sub.
        This is the main driver of the system - triggered by Nest state changes.
        """
        try:
            # Parse Nest event
            data = json.loads(message.data.decode("utf-8"))
            logger.info(f"[Controller] Processing Nest event: {data}")
            
            if "resourceUpdate" in data:
                resource = data["resourceUpdate"]
                device_name = resource.get("name", "")
                traits = resource.get("traits", {})
                
                # Store Nest device state in database (async)
                await self.database.store_nest_event(device_name, traits)
                
                # Publish Nest state to MQTT for other systems (async)
                mqtt_topic = f"nest/devices/{device_name}/state"
                await self.mqtt_client.publish(mqtt_topic, traits)
                
                # Check for automation triggers based on Nest changes
                await self.process_nest_automation(device_name, traits)
                
        except Exception as e:
            logger.error(f"[Controller] Error processing Nest event: {e}")
            raise
    
    async def check_automation_rules(self, device_id: str, old_value: Any, new_value: Any):
        """
        Check if device state changes should trigger automation rules.
        This runs when MQTT devices change state.
        """
        try:
            # Example: Turn on lights when motion detected
            if device_id == "motion_sensor" and new_value.get("motion") == True:
                logger.info("[Controller] Motion detected - turning on lights")
                await self.mqtt_client.publish("home/devices/lights/command", {"state": "on"})
            
            # Example: Adjust thermostat based on occupancy
            if device_id == "occupancy_sensor":
                occupancy = new_value.get("occupied", False)
                if occupancy:
                    logger.info("[Controller] Home occupied - adjusting thermostat")
                    await self.mqtt_client.publish("home/devices/thermostat/command", {
                        "temperature": 22, "mode": "heat"
                    })
                    
        except Exception as e:
            logger.error(f"[Controller] Error in automation rules: {e}")
    
    async def process_nest_automation(self, device_name: str, traits: Dict[str, Any]):
        """
        Process automation rules triggered by Nest device changes.
        This runs when Nest devices change state.
        """
        try:
            # Example: React to Nest thermostat changes
            if "sdm.devices.traits.Temperature" in traits:
                temp_data = traits["sdm.devices.traits.Temperature"]
                current_temp = temp_data.get("ambientTemperatureCelsius")
                
                if current_temp and current_temp < 18:  # Cold temperature
                    logger.info("[Controller] Cold temperature detected - sending alert")
                    await self.mqtt_client.publish("alerts/temperature", {
                        "device": device_name,
                        "temperature": current_temp,
                        "alert": "low_temperature"
                    })
                    
        except Exception as e:
            logger.error(f"[Controller] Error in Nest automation: {e}")
    
    def get_device_state(self, device_topic: str) -> Any:
        """Get the last known state of an MQTT device (synchronous)."""
        return self.mqtt_client.get_last_value(device_topic)
    
    def get_all_device_states(self) -> Dict[str, Any]:
        """Get all last known device states (synchronous)."""
        return self.mqtt_client.get_all_values()
    
    async def start(self):
        """Start the controller and all services."""
        self._running = True
        logger.info("[Controller] Starting Smart Home Controller...")
        
        try:
            # Start database connection
            await self.database.connect()
            
            # Start MQTT client (runs in background)
            mqtt_task = asyncio.create_task(self.mqtt_client.run_forever())
            
            # Start Pub/Sub listener with our Nest event handler
            pubsub_task = asyncio.create_task(
                self.pubsub_client.start_listening(callback=self.on_nest_event)
            )
            
            logger.info("[Controller] All services started")
            
            # Wait for tasks to complete
            await asyncio.gather(mqtt_task, pubsub_task)
            
        except Exception as e:
            logger.error(f"[Controller] Error starting controller: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the controller and cleanup resources."""
        logger.info("[Controller] Stopping Smart Home Controller...")
        self._running = False
        
        # Cleanup all services
        await self.mqtt_client.cleanup()
        await self.pubsub_client.cleanup()
        await self.database.disconnect()
        
        logger.info("[Controller] Controller stopped")

# Example usage
async def main():
    controller = SmartHomeController()
    
    try:
        await controller.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await controller.stop()

if __name__ == "__main__":
    asyncio.run(main())
