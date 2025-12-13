from fastapi import FastAPI

from src.api.health import router as health_router
from src.api.routers_v1 import router as v1_router
from src.config.lifespan import lifespan as lifespan_manager
from src.config.manager import settings
from src.core.middleware.handle_middleware import handle_middleware
from src.core.utils.exceptions.handler import handle_exceptions

app = FastAPI(lifespan=lifespan_manager, **settings.set_backend_app_attributes)
handle_exceptions(app)
handle_middleware(app)

app.include_router(health_router)
app.include_router(v1_router)
