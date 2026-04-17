from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import routes_auth
from app.core.config import settings
from app.db.session import engine
from app.db.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Высвобождает ресурсы приложения.

    Args:
        app (FastAPI): Приложение FastAPI.
    """
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(routes_auth.router)


@app.get("/health", tags=["system"])
async def health():
    """
    Получает статус системы и название окружения.
    """
    return {"status": "OK", "env": settings.env}
