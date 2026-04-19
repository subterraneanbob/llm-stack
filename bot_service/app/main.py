from fastapi import FastAPI

app = FastAPI(title="bot-service")


@app.get("/health", tags=["system"])
async def health():
    """
    Получает статус системы и название окружения.
    """
    return {"status": "OK", "env": "local"}
