from fastapi import FastAPI
from pydantic import EmailStr

# from src.config.lifespan import lifespan as lifespan_manager
from src.config.manager import settings
from src.core.utils.exceptions.handler import handle_exceptions

app = FastAPI(**settings.set_backend_app_attributes)

handle_exceptions(app)


@app.get("/")
async def health():
    return {"root": True}


@app.post("/ping")
async def ping(
    email: EmailStr,
    password: int,
):
    return {"ping": "pong"}
