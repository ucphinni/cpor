import asyncio
import json
import httpx
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String
from asyncio_mqtt import Client as MQTTClient, MqttError

# ---- SQLAlchemy Async Setup ----
Base = declarative_base()

class House(Base):
    __tablename__ = 'houses'
    id = Column(Integer, primary_key=True)
    description = Column(String)

DATABASE_URL = "sqlite+aiosqlite:///mvp.db"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ---- Async MQTT ----
async def mqtt_listener():
    try:
        async with MQTTClient("localhost") as client:
            await client.subscribe("#")
            async with client.unfiltered_messages() as messages:
                async for message in messages:
                    print(f"📨 MQTT Received on {message.topic}: {message.payload.decode()}")
    except MqttError as e:
        print(f"❌ MQTT error: {e}")


# ---- Async Google Nest Call (Placeholder) ----
async def call_google_nest():
    print("🌐 [Placeholder] Calling Google Nest API...")
    async with httpx.AsyncClient() as client:
        url = "https://smartdevicemanagement.googleapis.com/v1/enterprises/project-id/devices"
        headers = {"Authorization": "Bearer YOUR_ACCESS_TOKEN"}
        try:
            response = await client.get(url, headers=headers)
            print(f"✅ Google Nest response status: {response.status_code}")
            print(response.text)
        except Exception as e:
            print(f"❌ Google Nest call failed: {e}")


# ---- Controller ----
async def controller():
    print("🚀 Starting MVP-1 Controller")

    # 1️⃣ Database read/write
    async with async_session() as session:
        result = await session.execute(
            House.__table__.select().limit(1)
        )
        house_row = result.first()
        if not house_row:
            print("➕ No house found, adding one.")
            new_house = House(description="My MVP House")
            session.add(new_house)
            await session.commit()
        else:
            print(f"🏠 Found House in DB: {house_row[0].description}")

    # 2️⃣ Google Nest
    await call_google_nest()

    # 3️⃣ MQTT
    print("✅ MQTT listener starting...")
    await mqtt_listener()


# ---- Entry ----
async def main():
    await init_db()
    await controller()

if __name__ == "__main__":
    asyncio.run(main())