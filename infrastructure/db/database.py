

from sqlalchemy import create_engine
#from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData
import os
from dotenv import load_dotenv
load_dotenv()

db_user = os.getenv("DB_USER", "postgres")
db_password = os.getenv("DB_PASSWORD", "password")
db_host = os.getenv("DB_HOST", "psql") # psql #0.0.0.0
db_name = os.getenv("DB_NAME", "wallet_db")

DATABASE_URL_CONF = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}/{db_name}"

DATABASE = os.getenv("DATABASE_URL", DATABASE_URL_CONF)

engine = create_async_engine(DATABASE, echo=True, pool_size=0, max_overflow=-1, pool_timeout=360)

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