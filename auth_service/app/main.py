from fastapi import FastAPI


app = FastAPI()


@app.get("/health", tags=["system"])
async def health():
    """
    Получает статус системы и название окружения.
    """
    return {"status": "OK", "env": "dev"}
