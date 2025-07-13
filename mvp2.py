#!/usr/bin/env python3

"""
MVP2: Single-file async controller with Typer CLI
- Async SQLAlchemy (aiosqlite)
- Async gmqtt MQTT client
- Async Nest API placeholder (httpx)
- Configurable via env or CLI
- Graceful shutdown
"""

# Section 1: Imports & Config
import asyncio
import logging
import os
import signal
import json
from typing import Any, Dict, Protocol, Sequence
from datetime import datetime, timedelta
import typer
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import time

# Load environment variables from .env file
load_dotenv()

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, select

from gmqtt import Client as GMQTTClient  # type: ignore
import httpx

# MQTT Protocol Definitions
from typing import Any, Dict, Sequence, Callable, Union

# Define types that gmqtt uses
MQTTMessage = Dict[str, Any]
OnConnectCallback = Callable[[Any, Dict[str, Any], int, Dict[str, Any]], None]
OnMessageCallback = Callable[[Any, str, bytes, int, Dict[str, Any]], None]
OnDisconnectCallback = Callable[[Any, Any, Any], None]

class MQTTClientProtocol(Protocol):
    """Protocol defining the required MQTT client interface."""
    on_connect: OnConnectCallback
    on_message: OnMessageCallback
    on_disconnect: OnDisconnectCallback

    def set_auth_credentials(self, username: str | None, password: str | None) -> None: ...
    def subscribe(self, topic: Union[str, Sequence[str]], qos: int = 0, **kwargs: Any) -> None: ...
    async def connect(
        self,
        host: str,
        port: int = 1883,
        ssl: bool = False,
        keepalive: int = 60,
        version: int = 5,
        raise_exc: bool = True
    ) -> None: ...
    async def disconnect(self, reason_code: int = 0) -> None: ...

# CLI App
app = typer.Typer()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Environment / Config
DATABASE_URL = str(os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./test.db"))

# MQTT Config - Home Assistant defaults
MQTT_BROKER = str(os.environ.get("MQTT_BROKER", "192.168.8.241"))
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_USER = str(os.environ.get("MQTT_USER", "mqtt"))
MQTT_PASSWORD = str(os.environ.get("MQTT_PASSWORD", "mqtt"))
MQTT_USE_SSL = os.environ.get("MQTT_USE_SSL", "false").lower() == "true"
MQTT_TOPIC = str(os.environ.get("MQTT_TOPIC", "home/+/temperature"))
MQTT_CLIENT_ID = str(os.environ.get("MQTT_CLIENT_ID", "mvp2_client_cote"))

# Nest API Config - Using Device Access Console and OAuth2
NEST_ACCESS_TOKEN: str | None = str(os.environ.get("NEST_ACCESS_TOKEN")) if os.environ.get("NEST_ACCESS_TOKEN") is not None else None
NEST_PROJECT_ID: str = str(os.environ.get("NEST_PROJECT_ID"))
NEST_API_URL = "https://smartdevicemanagement.googleapis.com/v1"

# Google Cloud Pub/Sub Config
GCP_PROJECT_ID = str(os.environ.get("GCP_PROJECT_ID")) if os.environ.get("GCP_PROJECT_ID") is not None else None
PUBSUB_SUBSCRIPTION_ID = str(os.environ.get("PUBSUB_SUBSCRIPTION_ID")) if os.environ.get("PUBSUB_SUBSCRIPTION_ID") is not None else None

# Validate required environment variables
_required_env_vars = [
    "NEST_PROJECT_ID", "GCP_PROJECT_ID", "PUBSUB_SUBSCRIPTION_ID",
    "NEST_CLIENT_ID", "NEST_CLIENT_SECRET", "NEST_REFRESH_TOKEN"
]
_missing_vars = [var for var in _required_env_vars if not os.environ.get(var)]
if _missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(_missing_vars)}")
    logger.error("Please check your .env file and ensure all required variables are set")
    exit(1)

# Section 2: Token Management
class TokenManager:
    """Manages Google OAuth2 token refresh automatically."""
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token = None
        self.expires_at = None
        self._refresh_lock = asyncio.Lock()
        
    def _load_from_env(self):
        """Load current access token from environment."""
        load_dotenv()  # Reload environment
        self.access_token = str(os.getenv('NEST_ACCESS_TOKEN')) if os.getenv('NEST_ACCESS_TOKEN') is not None else None

    async def get_valid_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        async with self._refresh_lock:
            # Load current token from env if we don't have one
            if not self.access_token:
                self._load_from_env()
                
            # If we still don't have a token or it's expired/expiring soon, refresh
            if not self.access_token or self._is_token_expired():
                logger.info("[TokenManager] Token is missing or expired, refreshing...")
                await self._refresh_token()
                
            if not self.access_token:
                raise RuntimeError("Failed to obtain a valid access token.")
            return self.access_token
        
    def _is_token_expired(self) -> bool:
        """Check if the current token is expired or will expire soon."""
        if not self.expires_at:
            # If we don't know expiry, try to make a test request
            # For safety, assume it needs refresh
            logger.debug("[TokenManager] Token expiry unknown, will refresh")
            return True
        # Refresh 10 minutes before expiry to be safe
        buffer_time = timedelta(minutes=10)
        is_expired = datetime.now() >= (self.expires_at - buffer_time)
        if is_expired:
            logger.debug("[TokenManager] Token expires soon or has expired")
        return is_expired
        
    async def _refresh_token(self):
        """Refresh the access token using the refresh token."""
        try:
            logger.info("[TokenManager] Refreshing access token...")
            
            # Create credentials object
            creds = Credentials.from_authorized_user_info({
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token,
                'token_uri': 'https://oauth2.googleapis.com/token',
                'scopes': [
                    'https://www.googleapis.com/auth/sdm.service',
                    'https://www.googleapis.com/auth/pubsub'
                ]
            })

            # Refresh the token
            creds.refresh(Request())
            
            # Update our stored values
            self.access_token = creds.token
            # Google tokens typically expire in 1 hour
            self.expires_at = datetime.now() + timedelta(seconds=3600)
            
            # Update the .env file
            await self._update_env_file_async(self.access_token)
            
            logger.info("[TokenManager] Access token refreshed successfully, expires at %s", 
                       self.expires_at.strftime("%H:%M:%S"))
            
        except Exception as e:
            logger.error("[TokenManager] Failed to refresh token: %s", e)
            # Clear our stored token so we'll try again next time
            self.access_token = None
            self.expires_at = None
            raise
            
    async def _update_env_file_async(self, new_token: str):
        """Update the .env file with the new access token asynchronously."""
        def _update_env_sync():
            try:
                # Read current file
                if os.path.exists('.env'):
                    with open('.env', 'r') as f:
                        lines = f.readlines()
                else:
                    lines = []
                
                # Update or add the token line
                token_line_updated = False
                new_lines = []
                for line in lines:
                    if line.startswith('NEST_ACCESS_TOKEN='):
                        new_lines.append(f'NEST_ACCESS_TOKEN={new_token}\n')
                        token_line_updated = True
                    else:
                        new_lines.append(line)
                
                # If we didn't find an existing line, add it
                if not token_line_updated:
                    new_lines.append(f'NEST_ACCESS_TOKEN={new_token}\n')
                
                # Write back to file
                with open('.env', 'w') as f:
                    f.writelines(new_lines)
                    
                logger.debug("[TokenManager] Updated .env file with new token")
                
            except Exception as e:
                logger.warning("[TokenManager] Could not update .env file: %s", e)
        
        # Run the sync operation in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _update_env_sync)
        
    async def force_refresh(self):
        """Force a token refresh regardless of expiry time."""
        async with self._refresh_lock:
            await self._refresh_token()

# Section 3: SQLAlchemy DB Class
Base = declarative_base()

class House(Base):
    __tablename__ = "houses"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)

class Database:
    def __init__(self, db_url: str):
        self.engine = create_async_engine(db_url, echo=False)
        self.SessionLocal = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def init_db(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("[DB] Initialized.")

    async def add_house(self, name: str, description: str) -> None:
        async with self.SessionLocal() as session:
            stmt = select(House).where(House.name == name)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                logger.info("[DB] House already exists.")
                return
            house = House(name=name, description=description)
            session.add(house)
            await session.commit()
            logger.info(f"[DB] Added house: {name}")

    async def list_houses(self) -> Sequence[House]:
        async with self.SessionLocal() as session:
            stmt = select(House)
            result = await session.execute(stmt)
            houses = result.scalars().all()
            for h in houses:
                logger.info(f"[DB] House: id={h.id}, name={h.name}, desc={h.description}")
            return houses

# Section 3: MQTT Client Class
class MQTTClient:
    def __init__(
        self,
        broker: str,
        topic: str,
        client_id: str,
        port: int = 1883,
        username: str | None = None,
        password: str | None = None,
        use_ssl: bool = False
    ):
        """Initialize MQTT client with the given configuration."""
        self._handler = MQTTHandler(
            broker=broker,
            port=port,
            username=username,
            password=password,
            use_ssl=use_ssl,
            topic=topic
        )

    async def connect(self) -> None:
        """Connect to the MQTT broker."""
        await self._handler.connect()

    async def run_forever(self) -> None:
        """Keep the MQTT connection alive."""
        try:
            while True:
                await asyncio.sleep(10)  # Keep alive heartbeat
        except asyncio.CancelledError:
            pass

    async def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        await self._handler.disconnect()

# Section 4: Nest API Class
class NestAPI:
    """Google Nest SDM API client with automatic token refresh."""
    def __init__(self, base_url: str, project_id: str, token_manager: TokenManager):
        self.base_url = base_url
        self.project_id = project_id
        self.token_manager = token_manager
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=10.0,
            http2=True  # Enable HTTP/2 for better performance
        )

    async def _get_headers(self) -> Dict[str, str]:
        """Get headers with a valid access token."""
        token = await self.token_manager.get_valid_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def list_devices(self) -> Dict[str, Any]:
        """List all Nest devices in the project."""
        return await self._make_authenticated_request(
            "GET", f"/enterprises/{self.project_id}/devices"
        )

    async def get_device(self, device_id: str) -> Dict[str, Any]:
        """Get a specific device's details."""
        return await self._make_authenticated_request(
            "GET", f"/enterprises/{self.project_id}/devices/{device_id}"
        )

    async def set_temperature(self, device_id: str, heat: float | None = None, cool: float | None = None) -> None:
        """Set target temperature for a thermostat. Specify either heat, cool, or both."""
        if heat is None and cool is None:
            raise ValueError("Must specify at least one of heat or cool temperature")

        command = {
            "command": "sdm.devices.commands.ThermostatTemperatureSetpoint.SetRange",
            "params": {}
        }
        
        if heat is not None:
            command["params"]["heatCelsius"] = heat
        if cool is not None:
            command["params"]["coolCelsius"] = cool

        await self._make_authenticated_request(
            "POST", 
            f"/enterprises/{self.project_id}/devices/{device_id}:executeCommand",
            json_data=command
        )
        logger.info("[Nest] Set temperature for device %s: heat=%s, cool=%s",
                   device_id, heat, cool)

    async def _make_authenticated_request(self, method: str, endpoint: str, json_data: Dict[str, Any] | None = None, retry_count: int = 0) -> Dict[str, Any]:
        """Make an authenticated request with automatic token refresh on auth failures."""
        max_retries = 2
        
        try:
            headers = await self._get_headers()
            
            if method.upper() == "GET":
                response = await self.client.get(endpoint, headers=headers)
            elif method.upper() == "POST":
                response = await self.client.post(endpoint, headers=headers, json=json_data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            result = response.json()
            if method.upper() == "GET" and "devices" in result:
                logger.info("[Nest] Found %d devices", len(result.get("devices", [])))
            elif method.upper() == "GET":
                logger.info("[Nest] Got device: %s", result.get("name", "Unknown"))
                
            return result
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401 and retry_count < max_retries:
                logger.warning("[Nest] Authentication failed (401), refreshing token and retrying...")
                await self.token_manager.force_refresh()
                return await self._make_authenticated_request(method, endpoint, json_data, retry_count + 1)
            else:
                logger.error("[Nest] Request failed: %s %s - %s", method, endpoint, e)
                raise
        except httpx.HTTPError as e:
            logger.error("[Nest] Network error: %s", e)
            raise

    async def get_temperature(self, device_id: str) -> Dict[str, float]:
        """Get current and target temperatures for a thermostat."""
        try:
            device = await self.get_device(device_id)
            traits = device.get("traits", {})
            temp_data = {}
            
            if "sdm.devices.traits.Temperature" in traits:
                temp = traits["sdm.devices.traits.Temperature"]
                temp_data["ambient"] = temp.get("ambientTemperatureCelsius")
                
            if "sdm.devices.traits.ThermostatTemperatureSetpoint" in traits:
                setpoint = traits["sdm.devices.traits.ThermostatTemperatureSetpoint"]
                temp_data["heat"] = setpoint.get("heatCelsius")
                temp_data["cool"] = setpoint.get("coolCelsius")
                
            logger.info("[Nest] Device %s temperatures: %s", device_id, temp_data)
            return temp_data
        except httpx.HTTPError as e:
            logger.error("[Nest] Failed to get temperature: %s", e)
            raise

    async def close(self) -> None:
        await self.client.aclose()

# Section 4.5: Pub/Sub Event Handler
class PubSubClient:
    """Google Cloud Pub/Sub client for real-time Nest events using HTTP API."""
    def __init__(self, project_id: str, subscription_id: str, token_manager: TokenManager):
        self.project_id = project_id
        self.subscription_id = subscription_id
        self.token_manager = token_manager
        self._running = False
        
    async def _get_headers(self) -> Dict[str, str]:
        """Get headers with a valid access token."""
        token = await self.token_manager.get_valid_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
    async def start_listening(self, callback=None):
        """Start listening for Pub/Sub messages."""
        self._running = True
        logger.info("[PubSub] Starting to listen for Nest events...")
        consecutive_auth_failures = 0
        max_auth_failures = 3
        
        async with httpx.AsyncClient(timeout=60.0, http2=True) as client:
            while self._running:
                try:
                    # Pull messages from subscription
                    headers = await self._get_headers()
                    pull_url = f"https://pubsub.googleapis.com/v1/{self.subscription_id}:pull"
                    pull_data = {
                        "maxMessages": 10
                    }
                    
                    response = await client.post(pull_url, headers=headers, json=pull_data)
                    
                    if response.status_code == 200:
                        consecutive_auth_failures = 0  # Reset auth failure counter
                        data = response.json()
                        messages = data.get("receivedMessages", [])
                        
                        if messages:
                            logger.info(f"[PubSub] Received {len(messages)} messages")
                            
                            # Process messages
                            ack_ids = []
                            for msg in messages:
                                ack_ids.append(msg["ackId"])
                                if callback:
                                    await callback(msg)
                                else:
                                    await self._default_message_handler(msg)
                            
                            # Acknowledge messages
                            if ack_ids:
                                headers = await self._get_headers()
                                ack_url = f"https://pubsub.googleapis.com/v1/{self.subscription_id}:acknowledge"
                                ack_data = {"ackIds": ack_ids}
                                ack_response = await client.post(ack_url, headers=headers, json=ack_data)
                                if ack_response.status_code != 200:
                                    logger.warning(f"[PubSub] Failed to acknowledge messages: {ack_response.status_code}")
                        else:
                            # No messages, wait a bit before next pull
                            await asyncio.sleep(5)
                            
                    elif response.status_code == 401:
                        consecutive_auth_failures += 1
                        logger.warning(f"[PubSub] Authentication failed ({consecutive_auth_failures}/{max_auth_failures}) - refreshing token")
                        
                        if consecutive_auth_failures >= max_auth_failures:
                            logger.error("[PubSub] Too many consecutive auth failures, stopping listener")
                            break
                            
                        # Force token refresh
                        try:
                            await self.token_manager.force_refresh()
                            await asyncio.sleep(5)  # Brief pause before retry
                        except Exception as e:
                            logger.error(f"[PubSub] Failed to refresh token: {e}")
                            await asyncio.sleep(30)
                    else:
                        logger.warning(f"[PubSub] Pull request failed: {response.status_code} - {response.text}")
                        await asyncio.sleep(10)
                        
                except asyncio.TimeoutError:
                    logger.debug("[PubSub] Pull timeout, continuing...")
                except Exception as e:
                    logger.error(f"[PubSub] Error: {e}")
                    await asyncio.sleep(10)
    
    async def _default_message_handler(self, message):
        """Default handler for Pub/Sub messages."""
        import base64
        import json
        
        try:
            # Decode message data
            data = base64.b64decode(message["message"]["data"]).decode("utf-8")
            event_data = json.loads(data)
            
            logger.info(f"[PubSub] Nest event: {event_data}")
            
            # Extract device info
            if "resourceUpdate" in event_data:
                resource = event_data["resourceUpdate"]
                device_name = resource.get("name", "Unknown")
                traits = resource.get("traits", {})
                logger.info(f"[PubSub] Device {device_name} updated: {traits}")
                
        except Exception as e:
            logger.error(f"[PubSub] Failed to process message: {e}")
    
    def stop(self):
        """Stop listening for messages."""
        self._running = False
        logger.info("[PubSub] Stopping message listener...")

# Section 5: Controller Class
class Controller:
    def __init__(self, db: Database, mqtt: MQTTClient, nest: NestAPI, pubsub: PubSubClient | None = None):
        self.db = db
        self.mqtt = mqtt
        self.nest = nest
        self.pubsub = pubsub
        self._stop_event = asyncio.Event()
        self._tasks = []
        
        # Ensure pubsub and nest use the same token manager
        if self.pubsub and hasattr(self.nest, 'token_manager'):
            self.pubsub.token_manager = self.nest.token_manager

    async def start(self) -> None:
        logger.info("[Controller] Starting...")
        await self.db.init_db()
        await self.db.add_house("My House", "Primary residence")
        await self.db.list_houses()

        # Connect to MQTT
        await self.mqtt.connect()
        
        # Start periodic token refresh (every 45 minutes)
        token_refresh_task = asyncio.create_task(self._refresh_tokens_periodically())
        self._tasks.append(token_refresh_task)
        
        # Start periodic Nest device data fetching
        nest_task = asyncio.create_task(self._fetch_nest_data_periodically())
        self._tasks.append(nest_task)
        
        # Start Pub/Sub listener for real-time Nest events
        if self.pubsub:
            pubsub_task = asyncio.create_task(self.pubsub.start_listening())
            self._tasks.append(pubsub_task)

        # Keep MQTT connection alive
        mqtt_task = asyncio.create_task(self.mqtt.run_forever())
        self._tasks.append(mqtt_task)

        # Setup signal handlers
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))

        await self._stop_event.wait()

    async def _refresh_tokens_periodically(self):
        """Periodically refresh tokens to avoid expiration."""
        while not self._stop_event.is_set():
            try:
                # Wait 45 minutes (tokens expire in 60 minutes, so this gives us buffer)
                await asyncio.wait_for(self._stop_event.wait(), timeout=2700)  # 45 minutes
                break  # If stop event is set, exit loop
            except asyncio.TimeoutError:
                # Timeout reached, refresh token
                try:
                    logger.info("[Controller] Proactively refreshing access token...")
                    await self.nest.token_manager.force_refresh()
                    logger.info("[Controller] Token refreshed successfully")
                except Exception as e:
                    logger.error(f"[Controller] Failed to refresh token: {e}")

    async def _fetch_nest_data_periodically(self):
        """Periodically fetch Nest device data."""
        while not self._stop_event.is_set():
            try:
                logger.info("[Controller] Fetching Nest device data...")
                devices = await self.nest.list_devices()
                
                for device in devices.get("devices", []):
                    device_id = device["name"].split("/")[-1]
                    device_type = device.get("type", "")
                    
                    if "THERMOSTAT" in device_type:
                        temps = await self.nest.get_temperature(device_id)
                        current_temp = temps.get("ambient", 0)
                        logger.info(f"[Controller] Thermostat current temp: {current_temp:.1f}°C")
                        
                        # Here you could store data in database or send to MQTT
                        
            except Exception as e:
                logger.error(f"[Controller] Error fetching Nest data: {e}")
            
            # Wait 5 minutes before next fetch
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=300)
                break  # If stop event is set, exit loop
            except asyncio.TimeoutError:
                continue  # Timeout reached, continue with next iteration

    async def stop(self) -> None:
        logger.info("[Controller] Stopping...")
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        await self.mqtt.disconnect()
        if self.pubsub:
            self.pubsub.stop()
        await self.nest.close()
        self._stop_event.set()

# Section 6: Typer CLI Commands
@app.command()
def run(
    db_url: str = typer.Option(DATABASE_URL, help="Database URL"),
    mqtt_broker: str = typer.Option(MQTT_BROKER, help="MQTT Broker"),
    mqtt_port: int = typer.Option(MQTT_PORT, help="MQTT Port"),
    mqtt_user: str = typer.Option(MQTT_USER, help="MQTT Username"),
    mqtt_password: str = typer.Option(MQTT_PASSWORD, help="MQTT Password"),
    mqtt_use_ssl: bool = typer.Option(MQTT_USE_SSL, help="Use SSL for MQTT connection"),
    mqtt_topic: str = typer.Option(MQTT_TOPIC, help="MQTT Topic"),
    mqtt_client_id: str = typer.Option(MQTT_CLIENT_ID, help="MQTT Client ID"),
    nest_api_url: str = typer.Option(NEST_API_URL, help="Nest API Base URL"),
):
    """
    Run the full async controller.
    """
    async def _main() -> None:
        # Initialize TokenManager for automatic token refresh
        nest_client_id = str(os.getenv('NEST_CLIENT_ID'))
        nest_client_secret = str(os.getenv('NEST_CLIENT_SECRET'))
        nest_refresh_token = str(os.getenv('NEST_REFRESH_TOKEN'))
        
        if not all([nest_client_id, nest_client_secret, nest_refresh_token]):
            logger.error("[App] Missing required Nest OAuth credentials in environment")
            logger.error("[App] Required: NEST_CLIENT_ID, NEST_CLIENT_SECRET, NEST_REFRESH_TOKEN")
            return
            
        token_manager = TokenManager(nest_client_id, nest_client_secret, nest_refresh_token)
        
        db = Database(db_url)
        mqtt = MQTTClient(
            broker=mqtt_broker,
            port=mqtt_port,
            topic=mqtt_topic,
            client_id=mqtt_client_id,
            username=mqtt_user if mqtt_user else None,
            password=mqtt_password if mqtt_password else None,
            use_ssl=mqtt_use_ssl
        )
        nest = NestAPI(nest_api_url, NEST_PROJECT_ID, token_manager)
        
        # Initialize Pub/Sub client if credentials are available
        pubsub = None
        if GCP_PROJECT_ID and PUBSUB_SUBSCRIPTION_ID:
            pubsub = PubSubClient(GCP_PROJECT_ID, PUBSUB_SUBSCRIPTION_ID, token_manager)
            logger.info("[App] Pub/Sub client initialized for real-time events")
        else:
            logger.warning("[App] Pub/Sub not configured - missing credentials")
            
        controller = Controller(db, mqtt, nest, pubsub)
        await controller.start()

    try:
        asyncio.run(_main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("[App] Shutting down gracefully.")

@app.command()
def initdb(
    db_url: str = typer.Option(DATABASE_URL, help="Database URL"),
):
    """
    Initialize the database and create the House table.
    """
    async def _init() -> None:
        db = Database(db_url)
        await db.init_db()
        await db.add_house("My House", "Primary residence")

    asyncio.run(_init())

@app.command()
def listhouses(
    db_url: str = typer.Option(DATABASE_URL, help="Database URL"),
):
    """
    List all houses in the database.
    """
    async def _list() -> None:
        db = Database(db_url)
        await db.list_houses()

    asyncio.run(_list())

class MQTTHandler:
    def __init__(self, broker: str | None = None, port: int | None = None,
                username: str | None = None, password: str | None = None,
                use_ssl: bool | None = None, topic: str | None = None) -> None:
        self._client = GMQTTClient(MQTT_CLIENT_ID)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect
        self._client.on_subscribe = self._on_subscribe
        
        self._broker = broker or MQTT_BROKER
        self._port = port or MQTT_PORT
        self._username = username or MQTT_USER
        self._password = password or MQTT_PASSWORD
        self._use_ssl = use_ssl if use_ssl is not None else MQTT_USE_SSL
        self._topic = topic or MQTT_TOPIC
        self._connected = False
        
        # Disable our reconnection logic - let gmqtt handle it
        self._client.set_config({
            'reconnect_retries': -1,  # Infinite retries
            'reconnect_delay': 5,     # 5 second delay between retries
        })
        
        if self._username and self._password:
            self._client.set_auth_credentials(self._username, self._password)  # type: ignore

    def _log_with_time(self, msg: str, *args: Any) -> None:
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"[{now}] {msg}", *args)

    def _on_connect(self, client: MQTTClientProtocol, flags: Dict[str, Any], rc: int, properties: Dict[str, Any]) -> None:
        self._log_with_time("[MQTT] Connected with result code: %s", rc)
        self._connected = True
        self.subscribe(self._topic)

    def _on_subscribe(self, client: MQTTClientProtocol, mid: int, qos: tuple[int, ...], properties: Dict[str, Any]) -> None:
        self._log_with_time(f"[MQTT] Subscribed (mid={mid}, qos={qos})")

    def _on_disconnect(self, client: MQTTClientProtocol, packet: Any, exc: Exception | None = None) -> None:
        self._log_with_time("[MQTT] Disconnected (exc=%s) - gmqtt will handle reconnection", exc)
        self._connected = False
        if exc:
            self._log_with_time("[MQTT] Disconnection error: %s", exc)

    def _on_message(self, client: MQTTClientProtocol, topic: str, payload: bytes, qos: int, properties: Dict[str, Any]) -> None:
        try:
            self._log_with_time("[MQTT] Received message on %s: %s", topic, payload.decode())
        except Exception as e:
            self._log_with_time("[MQTT] Error in message callback: %s", e)

    def subscribe(self, topic: str, qos: int = 0) -> None:
        if self._connected:
            self._client.subscribe(topic, qos=qos)  # type: ignore
            self._log_with_time("[MQTT] Subscribed to %s", topic)

    async def connect(self) -> None:
        try:
            await self._client.connect(  # type: ignore
                self._broker,
                port=self._port,
                ssl=self._use_ssl,
                keepalive=60,  # Back to 60 seconds
                version=5
            )
            self._log_with_time("[MQTT] Connected to %s:%d (SSL=%s)", self._broker, self._port, self._use_ssl)
        except Exception as e:
            self._log_with_time("[MQTT] Connection failed: %s", e)
            raise

    async def disconnect(self) -> None:
        if self._connected:
            await self._client.disconnect()  # type: ignore
            self._connected = False
            self._log_with_time("[MQTT] Disconnected.")

@app.command()
def test_mqtt(
    broker: str = typer.Option(MQTT_BROKER, help="MQTT broker hostname/IP"),
    port: int = typer.Option(MQTT_PORT, help="MQTT broker port"),
    user: str = typer.Option(MQTT_USER, help="MQTT username"),
    password: str = typer.Option(MQTT_PASSWORD, help="MQTT password"),
    use_ssl: bool = typer.Option(MQTT_USE_SSL, help="Use SSL/TLS"),
    topic: str = typer.Option(MQTT_TOPIC, help="MQTT topic to subscribe to")
) -> None:
    """Test connection to Home Assistant MQTT broker."""
    
    async def test() -> None:
        handler = MQTTHandler(
            broker=broker,
            port=port,
            username=user,
            password=password,
            use_ssl=use_ssl,
            topic=topic
        )
        try:
            await handler.connect()
            logger.info("Successfully connected to MQTT broker!")
            logger.info("Press Ctrl+C to exit...")
            await asyncio.sleep(30)  # Keep connection open for 30 seconds
        except Exception as e:
            logger.error("Failed to connect: %s", e)
        finally:
            await handler.disconnect()

    try:
        asyncio.run(test())
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user.")

@app.command()
def test_nest(
    project_id: str = typer.Option(NEST_PROJECT_ID, help="Nest Device Access Project ID"),
) -> None:
    """Test connection to Nest API using automatic token refresh."""
    
    async def test() -> None:
        # Initialize TokenManager for automatic token refresh
        nest_client_id = str(os.getenv('NEST_CLIENT_ID'))
        nest_client_secret = str(os.getenv('NEST_CLIENT_SECRET'))
        nest_refresh_token = str(os.getenv('NEST_REFRESH_TOKEN'))
        
        if not all([nest_client_id, nest_client_secret, nest_refresh_token]):
            logger.error("[Test] Missing required Nest OAuth credentials in environment")
            logger.error("[Test] Required: NEST_CLIENT_ID, NEST_CLIENT_SECRET, NEST_REFRESH_TOKEN")
            return
            
        token_manager = TokenManager(nest_client_id, nest_client_secret, nest_refresh_token)
        
        nest = NestAPI(
            base_url=NEST_API_URL,
            project_id=project_id,
            token_manager=token_manager
        )
        try:
            # List all devices
            devices = await nest.list_devices()
            logger.info("\nNest Devices:")
            for device in devices.get("devices", []):
                device_id = device["name"].split("/")[-1]
                logger.info("-------------------")
                logger.info("Device ID: %s", device_id)
                logger.info("Type: %s", device.get("type", "unknown"))
                
                # Get temperature for thermostats
                if "sdm.devices.types.THERMOSTAT" in device.get("type", ""):
                    temps = await nest.get_temperature(device_id)
                    logger.info("Current Temperature: %.1f°C", temps.get("ambient", 0))
                    if "heat" in temps and temps["heat"] is not None:
                        logger.info("Heat Target: %.1f°C", temps["heat"])
                    if "cool" in temps and temps["cool"] is not None:
                        logger.info("Cool Target: %.1f°C", temps["cool"])
                
        except Exception as e:
            logger.error("Failed to test Nest API: %s", e)
        finally:
            await nest.close()

    try:
        asyncio.run(test())
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user.")

@app.command()
def refresh_token() -> None:
    """Manually refresh the Nest API access token."""
    
    async def refresh() -> None:
        # Initialize TokenManager
        nest_client_id = str(os.getenv('NEST_CLIENT_ID'))
        nest_client_secret = str(os.getenv('NEST_CLIENT_SECRET'))
        nest_refresh_token = str(os.getenv('NEST_REFRESH_TOKEN'))
        
        if not all([nest_client_id, nest_client_secret, nest_refresh_token]):
            logger.error("[Refresh] Missing required Nest OAuth credentials in environment")
            logger.error("[Refresh] Required: NEST_CLIENT_ID, NEST_CLIENT_SECRET, NEST_REFRESH_TOKEN")
            return
            
        token_manager = TokenManager(nest_client_id, nest_client_secret, nest_refresh_token)
        
        try:
            logger.info("[Refresh] Refreshing access token...")
            await token_manager.force_refresh()
            logger.info("[Refresh] Token refreshed successfully!")
        except Exception as e:
            logger.error(f"[Refresh] Failed to refresh token: {e}")

    try:
        asyncio.run(refresh())
    except KeyboardInterrupt:
        logger.info("\nRefresh interrupted by user.")

# Section 7: Main Entry
if __name__ == "__main__":
    app()
