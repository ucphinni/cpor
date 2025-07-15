"""Database operations and management."""
from typing import Sequence, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from .models import Base, House
from ..utils.logging import logger
from ..utils.retry import with_retry
from ..config.settings import DATABASE_URL

class Database:
    """Database manager for async SQLAlchemy operations."""
    def __init__(self, db_url: str = DATABASE_URL):
        self.engine = create_async_engine(db_url, echo=False)
        self.SessionLocal = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def init_db(self) -> None:
        """Initialize database and create tables."""
        async with self.engine.begin() as conn:
            try:
                await conn.run_sync(Base.metadata.create_all)
                logger.info("[DB] Initialized successfully")
            except Exception as e:
                logger.error(f"[DB] Initialization error: {e}")
                raise

    @with_retry(max_retries=3)
    async def add_house(self, name: str, description: str) -> None:
        """Add a new house to the database."""
        async with self.SessionLocal() as session:
            stmt = select(House).where(House.name == name)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                logger.info(f"[DB] House '{name}' already exists")
                return
                
            house = House(name=name, description=description)
            session.add(house)
            await session.commit()
            logger.info(f"[DB] Added house: {name}")

    @with_retry(max_retries=3)
    async def list_houses(self) -> Sequence[House]:
        """List all houses in the database."""
        async with self.SessionLocal() as session:
            stmt = select(House)
            result = await session.execute(stmt)
            houses = result.scalars().all()
            for house in houses:
                logger.info(f"[DB] House: id={house.id}, name={house.name}, desc={house.description}")
            return houses

    @with_retry(max_retries=3)
    async def update_device_state(self, device_id: str, state: dict) -> None:
        """Update device state in the database."""
        async with self.SessionLocal() as session:
            # For now, just log the device state update
            # In a real implementation, you'd have a Device table
            logger.info(f"[DB] Updated device {device_id} state: {state}")
            # TODO: Implement actual device state storage

    @with_retry(max_retries=3)
    async def store_nest_event(self, device_name: str, traits: dict) -> None:
        """Store Nest device event in the database."""
        async with self.SessionLocal() as session:
            # For now, just log the nest event
            # In a real implementation, you'd have a NestEvent table
            logger.info(f"[DB] Stored Nest event for {device_name}: {traits}")
            # TODO: Implement actual Nest event storage

    async def connect(self) -> None:
        """Connect to the database (initialize)."""
        await self.init_db()

    async def disconnect(self) -> None:
        """Disconnect from the database (cleanup)."""
        await self.cleanup()
            
    async def cleanup(self) -> None:
        """Clean up database resources."""
        await self.engine.dispose()
        logger.info("[DB] Resources cleaned up")
