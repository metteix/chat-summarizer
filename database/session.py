from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from configs.config import DB_URL

engine = create_async_engine(DB_URL, echo=True)

async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
