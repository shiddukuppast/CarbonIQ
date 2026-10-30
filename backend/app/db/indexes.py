import logging
from typing import Any

logger = logging.getLogger("carboniq.db.indexes")


async def create_database_indexes(db: Any) -> None:
    """
    Creates necessary MongoDB collection indexes for query performance,
    uniqueness, and workspace isolation.
    """
    try:
        # Users Collection: Unique Email
        await db.users.create_index("email", unique=True)
        await db.users.create_index("workspace_id")

        # Workspaces Collection
        await db.workspaces.create_index("id", unique=True)
        await db.workspaces.create_index("owner_id")

        # Electricity Records: Workspace isolation and reporting period filtering
        await db.electricity_records.create_index([("workspace_id", 1), ("reporting_month", -1)])
        await db.electricity_records.create_index("id", unique=True)

        # Transportation Records
        await db.transportation_records.create_index([("workspace_id", 1), ("date", -1)])
        await db.transportation_records.create_index("id", unique=True)

        # Bus Routes
        await db.bus_routes.create_index([("workspace_id", 1), ("status", 1)])
        await db.bus_routes.create_index("id", unique=True)

        # Waste Records
        await db.waste_records.create_index([("workspace_id", 1), ("date", -1)])
        await db.waste_records.create_index("id", unique=True)

        # Interventions / Proposals
        await db.interventions.create_index([("workspace_id", 1), ("status", 1)])
        await db.interventions.create_index("id", unique=True)

        logger.info("Successfully ensured all database indexes.")
    except Exception as exc:
        logger.warning(f"Could not initialize database indexes (might be mock or read-only connection): {exc}")
