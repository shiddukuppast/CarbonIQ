
import logging
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings
from app.db.indexes import create_database_indexes

logger = logging.getLogger("carboniq.db")


class MongoManager:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    is_connected: bool = False
    _test_db: Optional[Any] = None


mongo_manager = MongoManager()


async def connect_to_mongo() -> None:
    """
    Initializes the MongoDB connection pool using settings.MONGODB_URI.
    Handles startup errors gracefully without crashing the application.
    """
    if mongo_manager._test_db is not None:
        logger.info("Using configured test database fixture.")
        mongo_manager.is_connected = True
        return

    client = None

    try:
        logger.info(
            f"Connecting to MongoDB database: "
            f"{settings.MONGODB_DATABASE}..."
        )

        client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=15000,
            connectTimeoutMS=10000,
        )

        # Verify the connection
        await client.admin.command("ping")

        mongo_manager.client = client
        mongo_manager.db = client[settings.MONGODB_DATABASE]
        mongo_manager.is_connected = True

        logger.info("Successfully connected to MongoDB Atlas.")

        # Ensure database indexes
        await create_database_indexes(mongo_manager.db)

    except Exception as exc:
        mongo_manager.is_connected = False
        mongo_manager.db = None

        if client is not None:
            client.close()

        mongo_manager.client = None

        logger.error(
            f"Failed to connect to MongoDB "
            f"({settings.MONGODB_DATABASE}): {exc}. "
            "Application will start in disconnected/fallback mode."
        )


async def close_mongo_connection() -> None:
    """Closes MongoDB connection pool during shutdown."""
    if mongo_manager.client is not None:
        mongo_manager.client.close()
        mongo_manager.client = None
        mongo_manager.db = None
        mongo_manager.is_connected = False

        logger.info("Closed MongoDB connection pool.")


def get_database() -> Any:
    """
    Returns the active database instance.
    Falls back to test database if registered.
    """
    if mongo_manager._test_db is not None:
        return mongo_manager._test_db

    if mongo_manager.db is not None:
        return mongo_manager.db

    return None


def set_test_database(test_db: Any) -> None:
    """Allows test fixtures to inject an in-memory test database."""
    mongo_manager._test_db = test_db
    mongo_manager.is_connected = True


def reset_test_database() -> None:
    """Clears the test database override."""
    mongo_manager._test_db = None
