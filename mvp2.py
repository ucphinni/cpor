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
class MQTTClientProtocol(Protocol):
    """Protocol defining the required MQTT client interface."""
    on_connect: Any
    on_message: Any

    def subscribe(self, subscription_or_topic: str, qos: int = 0, **kwargs: Any) -> None: ...
    async def connect(
        self,
        host: str,
        port: int = 1883,
        ssl: bool = False,
        keepalive: int = 60,
        version: int = 5,
        raise_exc: bool = True
    ) -> None: ...
    async def disconnect(self, reason_code: int = 0, **properties: Dict[str, Any]) -> None: ...

# CLI App
app = typer.Typer()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment / Config
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
MQTT_BROKER = os.environ.get("MQTT_BROKER", "test.mosquitto.org")
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
    def __init__(self, broker: str, topic: str, client_id: str):
        self.broker = broker
        self.topic = topic
        self.client_id = client_id
        self.client: MQTTClientProtocol = GMQTTClient(self.client_id)

    def configure_callbacks(self) -> None:
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(
        self, 
        client: MQTTClientProtocol,
        flags: Dict[str, bool],
        rc: int,
        properties: Dict[str, str]
    ) -> None:
        """Called when client connects to broker."""
        logger.info("[MQTT] Connected. Subscribing...")
        client.subscribe(self.topic)

    def on_message(
        self,
        client: MQTTClientProtocol,
        topic: str,
        payload: bytes,
        qos: int,
        properties: Dict[str, str]
    ) -> None:
        """Called when message is received."""
        logger.info(f"[MQTT] Message: topic={topic}, payload={payload.decode()}")

    async def connect(self) -> None:
        self.configure_callbacks()
        await self.client.connect(
            host=self.broker,
            port=1883,
            ssl=False,
            keepalive=60,
            version=5
        )
        logger.info("[MQTT] Connected to broker.")

    async def run_forever(self) -> None:
        while True:
            await asyncio.sleep(1)

    async def disconnect(self) -> None:
        await self.client.disconnect(reason_code=0)
        logger.info("[MQTT] Disconnected.")

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
    mqtt_topic: str = typer.Option(MQTT_TOPIC, help="MQTT Topic"),
    mqtt_client_id: str = typer.Option(MQTT_CLIENT_ID, help="MQTT Client ID"),
    nest_api_url: str = typer.Option(NEST_API_URL, help="Nest API Base URL"),
):
    """
    Run the full async controller.
    """
    async def _main() -> None:
        db = Database(db_url)
        mqtt = MQTTClient(mqtt_broker, mqtt_topic, mqtt_client_id)
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

# Section 7: Main Entry
if __name__ == "__main__":
    app()
