#!/usr/bin/env python3
"""
Minimal async Nest controller: just 'run'.
- Loads all sensitive config from .env
- Uses HTTP/2 for Nest API
- Connects to MQTT and Pub/Sub
- Periodically fetches Nest device data
- Logs real-time events
- Uses async database (SQLite via SQLAlchemy)
"""
import os
import asyncio
import logging
from dotenv import load_dotenv
import httpx
from gmqtt import Client as GMQTTClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, select

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
NEST_PROJECT_ID = os.getenv("NEST_PROJECT_ID")
NEST_ACCESS_TOKEN = os.getenv("NEST_ACCESS_TOKEN")
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
PUBSUB_SUBSCRIPTION_ID = os.getenv("PUBSUB_SUBSCRIPTION_ID")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mvp3")

Base = declarative_base()
class House(Base):
    __tablename__ = "houses"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    desc = Column(String)

async def init_db():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.create_all)
            async with AsyncSession(engine) as session:
                result = await session.execute(select(House))
                houses = result.scalars().all()
                if not houses:
                    session.add(House(name="My House", desc="Primary residence"))
                    await session.commit()
                result = await session.execute(select(House))
                for house in result.scalars():
                    logger.info(f"House: id={house.id}, name={house.name}, desc={house.desc}")
        except Exception as e:
            logger.error(f"DB schema error: {e}. Dropping and recreating table.")
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
            async with AsyncSession(engine) as session:
                session.add(House(name="My House", desc="Primary residence"))
                await session.commit()
                result = await session.execute(select(House))
                for house in result.scalars():
                    logger.info(f"House: id={house.id}, name={house.name}, desc={house.desc}")
    return engine

async def fetch_nest_devices():
    url = f"https://smartdevicemanagement.googleapis.com/v1/enterprises/{NEST_PROJECT_ID}/devices"
    headers = {"Authorization": f"Bearer {NEST_ACCESS_TOKEN}"}
    async with httpx.AsyncClient(http2=True) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()

async def fetch_nest_periodically():
    while True:
        try:
            devices = await fetch_nest_devices()
            for device in devices.get("devices", []):
                device_id = device["name"].split("/")[-1]
                device_type = device.get("type", "")
                if "THERMOSTAT" in device_type:
                    logger.info(f"Thermostat: {device_id} {device_type}")
            logger.info(f"Nest devices: {devices}")
        except Exception as e:
            logger.error(f"Nest API error: {e}")
        await asyncio.sleep(300)  # 5 minutes

async def mqtt_connect_forever():
    mqtt = GMQTTClient("mvp3_client")
    if MQTT_USER and MQTT_PASSWORD:
        mqtt.set_auth_credentials(MQTT_USER, MQTT_PASSWORD)
    await mqtt.connect(MQTT_BROKER, port=MQTT_PORT)
    logger.info(f"Connected to MQTT {MQTT_BROKER}:{MQTT_PORT}")
    await mqtt.run_forever()

async def pubsub_listen():
    if not (GCP_PROJECT_ID and PUBSUB_SUBSCRIPTION_ID):
        logger.info("Pub/Sub not configured.")
        return
    logger.info(f"Listening to Pub/Sub subscription: {PUBSUB_SUBSCRIPTION_ID}")
    # Minimal: just log config. Real client would use google-cloud-pubsub
    while True:
        await asyncio.sleep(60)

async def run():
    logger.info("Starting minimal Nest controller...")
    engine = await init_db()
    await asyncio.gather(
        fetch_nest_periodically(),
        mqtt_connect_forever(),
        pubsub_listen()
    )

if __name__ == "__main__":
    asyncio.run(run())
