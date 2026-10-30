from typing import Any, Dict, List
from fastapi import APIRouter
from app.services.demo_service import (
    get_demo_dashboard,
    get_demo_electricity,
    get_demo_routes,
    get_demo_transportation,
    get_demo_waste,
)

router = APIRouter(prefix="/demo", tags=["Public Demo Access (Read-Only)"])


@router.get("/dashboard")
async def demo_dashboard() -> Dict[str, Any]:
    """Retrieves public read-only demonstration dashboard metrics."""
    return get_demo_dashboard()


@router.get("/electricity")
async def demo_electricity() -> List[Dict[str, Any]]:
    """Retrieves public read-only demonstration electricity records."""
    return get_demo_electricity()


@router.get("/transportation")
async def demo_transportation() -> List[Dict[str, Any]]:
    """Retrieves public read-only demonstration transportation records."""
    return get_demo_transportation()


@router.get("/waste")
async def demo_waste() -> List[Dict[str, Any]]:
    """Retrieves public read-only demonstration waste records."""
    return get_demo_waste()


@router.get("/routes")
async def demo_routes() -> List[Dict[str, Any]]:
    """Retrieves public read-only demonstration bus routes."""
    return get_demo_routes()
