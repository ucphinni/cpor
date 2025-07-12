import asyncio
from typing import Any, Dict, Optional, Protocol, Sequence, TypeAlias, Union, Callable, cast
from typing_extensions import TypedDict
from gmqtt import Client  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.engine.result import ScalarResult
import logging

# MQTT Protocol and Type Definitions
class MQTTMessage(Protocol):
    topic: str
    payload: bytes
    qos: int
    retain: bool
    dup: bool

class MQTTSubscription(TypedDict, total=False):
    topic: str
    qos: int
    no_local: bool
    retain_as_published: bool
    retain_handling_options: int

class MQTTClientProtocol(Protocol):
    on_connect: Optional[Callable[['MQTTClientProtocol', Dict[str, Any], int, Optional[Dict[str, Any]]], None]]
    on_message: Optional[Callable[['MQTTClientProtocol', str, bytes, int, Optional[Dict[str, Any]]], None]]

    def __init__(self, client_id: str) -> None: ...
    async def connect(
        self,
        host: str,
        port: int = 1883,
        ssl: bool = False,
        keepalive: int = 60,
        version: int = 5,
        raise_exc: bool = True
    ) -> None: ...
    async def disconnect(self, reason_code: int = 0, **properties: Any) -> None: ...
    def subscribe(
        self,
        topic_or_subscription: Union[str, MQTTSubscription, Sequence[MQTTSubscription]],
        qos: int = 0,
        **kwargs: Any
    ) -> None: ...

# Type aliases for better type checking
MQTTClient: TypeAlias = Client
SubscriptionType: TypeAlias = Union[str, MQTTSubscription, Sequence[MQTTSubscription]]

# MQTT Constants
MQTTv50: int = 5  # MQTT Protocol version 5.0

# Configure logging
logging.basicConfig(level=logging.INFO)

# SQLAlchemy Async setup
DATABASE_URL = "sqlite+aiosqlite:///./test.db"
Base = declarative_base()

class House(Base):
    __tablename__ = "houses"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# MQTT client details
MQTT_BROKER = "test.mosquitto.org"  # Replace with your broker
MQTT_CLIENT_ID = "mvp_gmqtt_client_cote"
MQTT_TOPIC = "home/+/temperature"  # example wildcard topic

# Placeholder for Nest API async call
async def set_nest_target_temperature(house_id: int, target_temp: float):
    # TODO: Implement actual Nest API call here with aiohttp or httpx
    # For MVP, just log the call
    logging.info(f"[Nest API] Setting target temp {target_temp} for house {house_id}")

# Async DB helpers
async def create_db_and_sample_house() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    
    async with AsyncSessionLocal() as session:
        stmt = select(House).where(House.name == "My House")
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing is None:
            house = House(name="My House", description="Primary residence")
            session.add(house)
            await session.commit()
            logging.info("Created sample house in DB")

async def print_houses() -> None:
    async with AsyncSessionLocal() as session:
        stmt = select(House)
        result: ScalarResult[House] = (await session.execute(stmt)).scalars()
        houses: Sequence[House] = result.all()
        stmt = select(House)
        result: ScalarResult[House] = (await session.execute(stmt)).scalars()
        houses: Sequence[House] = result.all()
        for house in houses:
            logging.info(f"House: id={house.id} name={house.name} desc={house.description}")

# MQTT callbacks
def on_connect(client: MQTTClientProtocol, flags: Dict[str, Any], rc: int, properties: Optional[Dict[str, Any]]) -> None:
    """Called when the client connects to the broker.
    
    Args:
        client: MQTT client instance
        flags: Connection flags from broker
        rc: Return code, 0 indicates success
        properties: Optional MQTT v5.0 properties
    """
    logging.info("Connected to MQTT Broker")
    client.subscribe(MQTT_TOPIC)

def on_message(
    client: MQTTClientProtocol,
    topic: str,
    payload: bytes,
    qos: int,
    properties: Optional[Dict[str, Any]]
) -> None:
    """Called when a message is received from the broker.
    
    Args:
        client: MQTT client instance
        topic: The topic the message was received on
        payload: Message payload as bytes
        qos: Quality of Service level
        properties: Optional MQTT v5.0 properties
    """
    logging.info(f"Received message on topic {topic}: {payload.decode()}")

async def main() -> None:
    """Main entry point for the application."""
    # Setup DB and print sample data
    await create_db_and_sample_house()
    await print_houses()

    # Setup MQTT client
    client = cast(MQTTClientProtocol, Client(MQTT_CLIENT_ID))
    client.on_connect = on_connect
    client.on_message = on_message

    await client.connect(
        host=MQTT_BROKER,
        port=1883,
        ssl=False,
        keepalive=60,
        version=MQTTv50
    )
    await client.connect(
        host=MQTT_BROKER,
        port=1883,
        ssl=False,
        keepalive=60,
        version=MQTTv50
    )

    # Run forever
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logging.info("Disconnecting MQTT client")
        await client.disconnect(reason_code=0)
        await client.disconnect(reason_code=0)

if __name__ == "__main__":
    asyncio.run(main())