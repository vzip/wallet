

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://default_user:default_pass@localhost/default_db")

# DATABASE_URL = 'postgresql+asyncpg://admin:Dezya201188@localhost/wallet_db'
engine = create_async_engine(DATABASE_URL, echo=True)

Base = declarative_base()

AsyncSessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

async def create_tables():
   
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)