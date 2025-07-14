"""Configuration management for the application."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database settings
DATABASE_URL = str(os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db"))

# Nest API settings
NEST_PROJECT_ID = str(os.getenv("NEST_PROJECT_ID"))
NEST_ACCESS_TOKEN = str(os.getenv("NEST_ACCESS_TOKEN"))
NEST_CLIENT_ID = str(os.getenv("NEST_CLIENT_ID"))
NEST_CLIENT_SECRET = str(os.getenv("NEST_CLIENT_SECRET"))
NEST_REFRESH_TOKEN = str(os.getenv("NEST_REFRESH_TOKEN"))
NEST_API_URL = "https://smartdevicemanagement.googleapis.com/v1"

# MQTT settings
MQTT_BROKER = str(os.getenv("MQTT_BROKER", "192.168.8.241"))
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = str(os.getenv("MQTT_USER", "mqtt"))
MQTT_PASSWORD = str(os.getenv("MQTT_PASSWORD", "mqtt"))
MQTT_USE_SSL = os.getenv("MQTT_USE_SSL", "false").lower() == "true"
MQTT_TOPIC = str(os.getenv("MQTT_TOPIC", "home/+/temperature"))
MQTT_CLIENT_ID = str(os.getenv("MQTT_CLIENT_ID", "mvp2_client_cote"))

# Google Cloud Pub/Sub settings
GCP_PROJECT_ID = str(os.getenv("GCP_PROJECT_ID"))
PUBSUB_SUBSCRIPTION_ID = str(os.getenv("PUBSUB_SUBSCRIPTION_ID"))

# Validate required environment variables
_required_env_vars = [
    "NEST_PROJECT_ID", "GCP_PROJECT_ID", "PUBSUB_SUBSCRIPTION_ID",
    "NEST_CLIENT_ID", "NEST_CLIENT_SECRET", "NEST_REFRESH_TOKEN"
]

def validate_config():
    """Validate that all required environment variables are set."""
    missing_vars = [var for var in _required_env_vars if not os.environ.get(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
