from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings

# Wait, sync engine or async engine? We requested async overall, so maybe asyncpg with async session.
# Let's use standard sync for simplicity and robust pg driver unless performance demands async. 
# AI instructions: "FastAPI Backend (async)", let's do async! But I added psycopg2 in requirements. 
# It's fine to stick with asyncpg as installed in requirements.txt (I added asyncpg).

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Fix the URL for asyncpg
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=0
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session
