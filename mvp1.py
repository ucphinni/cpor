import asyncio
from typing import Any, Dict, Optional, Sequence
from gmqtt import Client as MQTTClient
from gmqtt.mqtt.constants import MQTTv50
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.engine.result import ScalarResult
import logging

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
        for house in houses:
            logging.info(f"House: id={house.id} name={house.name} desc={house.description}")

# MQTT callbacks
def on_connect(client: MQTTClient, flags: Dict[str, Any], rc: int, properties: Optional[Dict[str, Any]]) -> None:
    logging.info("Connected to MQTT Broker")
    client.subscribe(MQTT_TOPIC)

def on_message(
    client: MQTTClient,
    topic: str,
    payload: bytes,
    qos: int,
    properties: Optional[Dict[str, Any]]
) -> None:
    logging.info(f"Received message on topic {topic}: {payload.decode()}")

async def main() -> None:
    # Setup DB and print sample data
    await create_db_and_sample_house()
    await print_houses()

    # Setup MQTT client
    client = MQTTClient(MQTT_CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message

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

if __name__ == "__main__":
    asyncio.run(main())