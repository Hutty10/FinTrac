import logging
from contextlib import asynccontextmanager

from src.core.cache_manager import cache_manager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    print("Starting up...")
    await cache_manager.initialize()
    logger.info("Cache manager initialized")
    yield
    print("Shutting down...")
    await cache_manager.close()
    logger.info("Cache manager shutdown complete")
