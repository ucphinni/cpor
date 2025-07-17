"""Configuration management for the application."""
import json
from pathlib import Path

# Load configuration from config.json
CONFIG_PATH = Path(__file__).parent.parent.parent / "config.json"
with open(CONFIG_PATH, "r") as config_file:
    config = json.load(config_file)

# Database settings
DATABASE_URL = config.get("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

# Nest API settings
NEST_PROJECT_ID = config.get("NEST_PROJECT_ID")
NEST_ACCESS_TOKEN = config.get("NEST_ACCESS_TOKEN")
NEST_CLIENT_ID = config.get("NEST_CLIENT_ID")
NEST_CLIENT_SECRET = config.get("NEST_CLIENT_SECRET")
NEST_REFRESH_TOKEN = config.get("NEST_REFRESH_TOKEN")
NEST_API_URL = "https://smartdevicemanagement.googleapis.com/v1"

# MQTT Broker configurations
BROKER_CONFIGS = config.get("MQTT_BROKERS", [])

# Google Cloud Pub/Sub settings
GCP_PROJECT_ID = config.get("GCP_PROJECT_ID")
PUBSUB_SUBSCRIPTION_ID = config.get("PUBSUB_SUBSCRIPTION_ID")
