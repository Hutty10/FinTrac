import logging
from contextlib import asynccontextmanager

from src.core.cache_manager import cache_manager
from src.core.utils.exceptions.cache import RedisConnectionError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    print("Starting up...")
    try:
        await cache_manager.initialize()
        logger.info("Cache manager initialized")
    except RedisConnectionError:
        logger.error("Unable to load redis")
    yield
    print("Shutting down...")
    await cache_manager.close()
    logger.info("Cache manager shutdown complete")
