from typing import Optional, Dict, List
from pathlib import Path

# Example: broker_id -> list of zigbee2mqtt topic prefixes
BROKER_ZIGBEE2MQTT_TOPICS: Dict[str, List[str]] = {}


def register_broker_topics(broker_id: str, topics: List[str]) -> None:
    """
    Register Zigbee2MQTT topic prefixes for a broker.
    """
    BROKER_ZIGBEE2MQTT_TOPICS[broker_id] = topics


def extract_zigbee_friendly_name(topic: str, broker_id: str) -> Optional[str]:
    """
    Extract the Zigbee2MQTT friendly device name from a topic string for a given broker.
    Args:
        topic (str): The MQTT topic string.
        broker_id (str): The broker identifier (e.g., host, client_id).
    Returns:
        Optional[str]: The Zigbee2MQTT friendly device name, or None if not found.
    """
    prefixes = BROKER_ZIGBEE2MQTT_TOPICS.get(broker_id, [])
    for base in prefixes:
        prefix = base + "/"
        if topic.startswith(prefix):
            parts = topic[len(prefix):].split("/")
            if parts:
                return parts[0]
    return None
