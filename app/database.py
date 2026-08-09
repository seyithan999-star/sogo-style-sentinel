from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.database_url, pool_pre_ping=True, pool_size=5, max_overflow=5)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


async def init_db():
    """İlk kurulum kolaylığı: tabloları oluşturur (production'da alembic migration tercih edilir)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
