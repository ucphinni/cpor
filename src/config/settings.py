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

# Helper to load X brokers from env
BROKER_CONFIGS = []
# First check if there's a broker without number (legacy support)
if os.getenv("MQTT_BROKER"):
    config = {
        "broker": os.getenv("MQTT_BROKER"),
        "port": int(os.getenv("MQTT_PORT", "1883")),
        "username": os.getenv("MQTT_USER", "mqtt"),
        "password": os.getenv("MQTT_PASSWORD", "mqtt"),
        "use_ssl": os.getenv("MQTT_USE_SSL", "false").lower() == "true",
        "topic": os.getenv("MQTT_TOPIC", "zigbee2mqtt/#"),
        "client_id": os.getenv("MQTT_CLIENT_ID", "mvp2_client_cote"),
        "zigbee2mqtt_topics": [t.strip() for t in os.getenv("ZIGBEE2MQTT_TOPICS", "zigbee2mqtt").split(",") if t.strip()],
        "mqtt_version": int(os.getenv("MQTT_VERSION", "311")),
    }
    BROKER_CONFIGS.append(config)

# Then check numbered brokers (MQTT_BROKER1, MQTT_BROKER2, etc.)
for i in range(1, 100):  # Support up to 99 numbered brokers
    broker = os.getenv(f"MQTT_BROKER{i}")
    if not broker:
        continue
    config = {
        "broker": broker,
        "port": int(os.getenv(f"MQTT_PORT{i}", "1883")),
        "username": os.getenv(f"MQTT_USER{i}", "mqtt"),
        "password": os.getenv(f"MQTT_PASSWORD{i}", "mqtt"),
        "use_ssl": os.getenv(f"MQTT_USE_SSL{i}", "false").lower() == "true",
        "topic": os.getenv(f"MQTT_TOPIC{i}", "zigbee2mqtt/#"),
        "client_id": os.getenv(f"MQTT_CLIENT_ID{i}", f"mvp2_client_cote_{i}"),
        "zigbee2mqtt_topics": [t.strip() for t in os.getenv(f"ZIGBEE2MQTT_TOPICS{i}", "zigbee2mqtt").split(",") if t.strip()],
        "mqtt_version": int(os.getenv(f"MQTT_VERSION{i}", "311")),
    }
    BROKER_CONFIGS.append(config)

# Legacy single broker settings for backward compatibility
MQTT_BROKER = BROKER_CONFIGS[0]["broker"] if BROKER_CONFIGS else "192.168.8.241"
MQTT_PORT = BROKER_CONFIGS[0]["port"] if BROKER_CONFIGS else 1883
MQTT_USER = BROKER_CONFIGS[0]["username"] if BROKER_CONFIGS else "mqtt"
MQTT_PASSWORD = BROKER_CONFIGS[0]["password"] if BROKER_CONFIGS else "mqtt"
MQTT_USE_SSL = BROKER_CONFIGS[0]["use_ssl"] if BROKER_CONFIGS else False
MQTT_TOPIC = BROKER_CONFIGS[0]["topic"] if BROKER_CONFIGS else "zigbee2mqtt/#"

# Legacy Zigbee2MQTT topics (now deprecated, use broker-specific configs)
ZIGBEE2MQTT_TOPICS = BROKER_CONFIGS[0]["zigbee2mqtt_topics"] if BROKER_CONFIGS else ["zigbee2mqtt"]

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
