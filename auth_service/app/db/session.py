from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings


DATABASE_URL = f"sqlite+aiosqlite:///{settings.sqlite_path}"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine)
