from typing import Any, Dict, List, Optional
from app.calculations.route_optimizer import RouteOptimizationProposal, optimize_bus_routes
from app.core.exceptions import EntityNotFoundException
from app.schemas.bus_route import (
    BusRouteCreateRequest,
    BusRouteResponse,
    BusRouteUpdateRequest,
    RouteOptimizationResponse,
)
from app.utils.dates import utc_iso
from app.utils.ids import generate_id


async def create_bus_route(
    req: BusRouteCreateRequest,
    workspace_id: str,
    user_id: str,
    db: Any,
) -> BusRouteResponse:
    now = utc_iso()
    route_id = generate_id("route")
    doc = {
        "id": route_id,
        "workspace_id": workspace_id,
        "creator_id": user_id,
        "route_name": req.route_name.strip(),
        "start_location": req.start_location.strip(),
        "destination": req.destination.strip(),
        "intermediate_stops": [s.strip() for s in req.intermediate_stops if s.strip()],
        "distance_km": req.distance_km,
        "duration_minutes": req.duration_minutes,
        "trips_per_day": req.trips_per_day,
        "operating_days_per_week": req.operating_days_per_week,
        "assigned_students": req.assigned_students,
        "bus_id": req.bus_id.strip(),
        "fuel_type": req.fuel_type,
        "fuel_efficiency_km_per_l": req.fuel_efficiency_km_per_l,
        "fuel_consumption_per_day_liters": req.fuel_consumption_per_day_liters,
        "seating_capacity": req.seating_capacity,
        "current_buses_count": req.current_buses_count,
        "status": req.status,
        "notes": req.notes,
        "created_at": now,
        "updated_at": now,
    }
    await db.bus_routes.insert_one(doc)
    return BusRouteResponse(**doc)


async def list_bus_routes(
    workspace_id: str,
    db: Any,
    skip: int = 0,
    limit: int = 100,
) -> List[BusRouteResponse]:
    cursor = db.bus_routes.find({"workspace_id": workspace_id}).sort("created_at", -1).skip(skip).limit(limit)
    routes = []
    async for item in cursor:
        item.pop("_id", None)
        routes.append(BusRouteResponse(**item))
    return routes


async def get_bus_route(
    route_id: str,
    workspace_id: str,
    db: Any,
) -> BusRouteResponse:
    doc = await db.bus_routes.find_one({"id": route_id, "workspace_id": workspace_id})
    if not doc:
        raise EntityNotFoundException(f"Bus route {route_id} not found.")
    doc.pop("_id", None)
    return BusRouteResponse(**doc)


async def update_bus_route(
    route_id: str,
    req: BusRouteUpdateRequest,
    workspace_id: str,
    db: Any,
) -> BusRouteResponse:
    doc = await db.bus_routes.find_one({"id": route_id, "workspace_id": workspace_id})
    if not doc:
        raise EntityNotFoundException(f"Bus route {route_id} not found.")

    updates: Dict[str, Any] = {"updated_at": utc_iso()}
    for field, val in req.model_dump(exclude_unset=True).items():
        if val is not None:
            updates[field] = val

    await db.bus_routes.update_one({"id": route_id, "workspace_id": workspace_id}, {"$set": updates})
    updated_doc = await db.bus_routes.find_one({"id": route_id, "workspace_id": workspace_id})
    updated_doc.pop("_id", None)
    return BusRouteResponse(**updated_doc)


async def delete_bus_route(
    route_id: str,
    workspace_id: str,
    db: Any,
) -> bool:
    res = await db.bus_routes.delete_one({"id": route_id, "workspace_id": workspace_id})
    if res.deleted_count == 0:
        raise EntityNotFoundException(f"Bus route {route_id} not found.")
    return True


async def optimize_workspace_bus_routes(
    workspace_id: str,
    db: Any,
    route_ids: Optional[List[str]] = None,
) -> RouteOptimizationResponse:
    if route_ids is not None:
        routes = []
        for rid in route_ids:
            clean_id = str(rid).strip() if rid is not None else ""
            if not clean_id:
                raise EntityNotFoundException("Invalid or empty bus route ID.")
            doc = await db.bus_routes.find_one({"id": clean_id, "workspace_id": workspace_id})
            if not doc:
                raise EntityNotFoundException(f"Bus route '{clean_id}' not found.")
            doc.pop("_id", None)
            routes.append(doc)

        proposals = optimize_bus_routes(routes, is_targeted=True)
        return RouteOptimizationResponse(
            proposals=proposals,
            analyzed_routes_count=len(routes),
            timestamp=utc_iso(),
        )

    cursor = db.bus_routes.find({"workspace_id": workspace_id, "status": "active"})
    routes = []
    async for item in cursor:
        item.pop("_id", None)
        routes.append(item)

    proposals = optimize_bus_routes(routes, is_targeted=False)
    return RouteOptimizationResponse(
        proposals=proposals,
        analyzed_routes_count=len(routes),
        timestamp=utc_iso(),
    )


async def save_proposal_as_intervention(
    proposal: RouteOptimizationProposal,
    workspace_id: str,
    user_id: str,
    db: Any,
) -> Dict[str, Any]:
    """
    Saves an accepted optimization proposal as a planned intervention.
    Does NOT modify live bus schedules or student assignments automatically.
    """
    now = utc_iso()
    intervention_id = generate_id("intv")
    doc = {
        "id": intervention_id,
        "workspace_id": workspace_id,
        "creator_id": user_id,
        "proposal_id": proposal.id,
        "title": proposal.title,
        "category": "Transportation",
        "description": proposal.summary,
        "estimated_benefit": (
            f"Save ~{proposal.estimated_fuel_savings_liters} L diesel/mo "
            f"(₹{proposal.estimated_monthly_savings_inr}/mo, {proposal.estimated_emissions_reduction_kg} kg CO2e/mo)"
        ),
        "estimated_cost_savings_inr": proposal.estimated_monthly_savings_inr,
        "estimated_emissions_savings_kg": proposal.estimated_emissions_reduction_kg,
        "status": "accepted_for_planning",
        "assumptions": proposal.assumptions,
        "actual_result": None,
        "created_at": now,
        "updated_at": now,
    }
    await db.interventions.insert_one(doc)
    doc.pop("_id", None)
    return doc
