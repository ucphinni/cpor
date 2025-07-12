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
from typing import Any, Dict, Protocol, Sequence
import typer
from dotenv import load_dotenv

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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment / Config
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

# MQTT Config - Home Assistant defaults
MQTT_BROKER = os.environ.get("MQTT_BROKER", "homeassistant.local")  # or use your HA IP
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_USER = os.environ.get("MQTT_USER", "")  # Set your MQTT username
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", "")  # Set your MQTT password
MQTT_USE_SSL = os.environ.get("MQTT_USE_SSL", "false").lower() == "true"
MQTT_TOPIC = os.environ.get("MQTT_TOPIC", "home/+/temperature")
MQTT_CLIENT_ID = os.environ.get("MQTT_CLIENT_ID", "mvp2_client_cote")

NEST_API_URL = os.environ.get("NEST_API_URL", "https://example-nest-api")

# Section 2: SQLAlchemy DB Class
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
        """Run the client forever."""
        while True:
            await asyncio.sleep(1)

    async def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        await self._handler.disconnect()

# Section 4: Nest API Class
class NestAPI:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=10.0)

    async def set_target_temperature(self, house_id: int, target: float) -> None:
        # MVP placeholder - replace with real call
        logger.info(f"[NestAPI] Set target temp to {target} for house {house_id}")
        # Example (disabled for MVP)
        # await self.client.post(f"{self.base_url}/set_temp", json={"house_id": house_id, "target": target})

    async def close(self) -> None:
        await self.client.aclose()

# Section 5: Controller Class
class Controller:
    def __init__(self, db: Database, mqtt: MQTTClient, nest: NestAPI):
        self.db = db
        self.mqtt = mqtt
        self.nest = nest
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        logger.info("[Controller] Starting...")
        await self.db.init_db()
        await self.db.add_house("My House", "Primary residence")
        await self.db.list_houses()

        await self.mqtt.connect()

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))

        await self._stop_event.wait()

    async def stop(self) -> None:
        logger.info("[Controller] Stopping...")
        await self.mqtt.disconnect()
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
        nest = NestAPI(nest_api_url)
        controller = Controller(db, mqtt, nest)
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
        
        # Use parameters if provided, otherwise use environment values
        self._broker = broker or MQTT_BROKER
        self._port = port or MQTT_PORT
        self._username = username or MQTT_USER
        self._password = password or MQTT_PASSWORD
        self._use_ssl = use_ssl if use_ssl is not None else MQTT_USE_SSL
        self._topic = topic or MQTT_TOPIC
        
        if self._username and self._password:
            self._client.set_auth_credentials(self._username, self._password)  # type: ignore

    def _on_connect(self, client: MQTTClientProtocol, flags: Dict[str, Any], rc: int, properties: Any) -> None:
        logger.info("[MQTT] Connected with result code: %s", rc)
        # Subscribe to topic on connect
        self.subscribe(self._topic)

    def _on_disconnect(self, client: MQTTClientProtocol, packet: Any, exc: Any = None) -> None:
        logger.info("[MQTT] Disconnected")
        if exc:
            logger.error("[MQTT] Disconnection error: %s", exc)

    def _on_message(self, client: MQTTClientProtocol, topic: str, payload: bytes, qos: int, properties: Any) -> None:
        logger.info("[MQTT] Received message on %s: %s", topic, payload.decode())

    def subscribe(self, topic: str, qos: int = 0) -> None:
        """Subscribe to a topic."""
        self._client.subscribe(topic, qos=qos)  # type: ignore
        logger.info("[MQTT] Subscribed to %s", topic)

    async def connect(self) -> None:
        """Connect to the MQTT broker."""
        try:
            await self._client.connect(  # type: ignore
                self._broker,
                port=self._port,
                ssl=self._use_ssl,
                version=5
            )
            logger.info("[MQTT] Connected to %s:%d (SSL=%s)", 
                       self._broker, self._port, self._use_ssl)
        except Exception as e:
            logger.error("[MQTT] Connection failed: %s", e)
            raise

    async def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        await self._client.disconnect()  # type: ignore
        logger.info("[MQTT] Disconnected.")

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

# Section 7: Main Entry
if __name__ == "__main__":
    app()
