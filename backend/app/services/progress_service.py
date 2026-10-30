from typing import Any, Dict, List
from app.core.exceptions import EntityNotFoundException
from app.schemas.progress import (
    GoalCreateRequest,
    GoalResponse,
    InterventionCreateRequest,
    InterventionResponse,
)
from app.utils.dates import utc_iso
from app.utils.ids import generate_id


async def create_goal(req: GoalCreateRequest, workspace_id: str, db: Any) -> GoalResponse:
    now = utc_iso()
    goal_id = generate_id("goal")
    doc = {
        "id": goal_id,
        "workspace_id": workspace_id,
        "goal_name": req.goal_name.strip(),
        "category": req.category,
        "baseline_value": req.baseline_value,
        "target_value": req.target_value,
        "target_period": req.target_period,
        "unit": req.unit,
        "current_value": req.baseline_value,
        "progress_percentage": 0.0,
        "status": "in_progress",
        "created_at": now,
        "updated_at": now,
    }
    await db.goals.insert_one(doc)
    return GoalResponse(**doc)


async def list_goals(workspace_id: str, db: Any) -> List[GoalResponse]:
    cursor = db.goals.find({"workspace_id": workspace_id}).sort("created_at", -1)
    goals = []
    async for item in cursor:
        item.pop("_id", None)
        goals.append(GoalResponse(**item))
    return goals


async def create_intervention(req: InterventionCreateRequest, workspace_id: str, db: Any) -> InterventionResponse:
    now = utc_iso()
    intv_id = generate_id("intv")
    doc = {
        "id": intv_id,
        "workspace_id": workspace_id,
        "title": req.title.strip(),
        "category": req.category,
        "proposal_id": req.proposal_id,
        "description": req.description,
        "estimated_benefit": req.estimated_benefit,
        "estimated_cost_savings_inr": req.estimated_cost_savings_inr,
        "estimated_emissions_savings_kg": req.estimated_emissions_savings_kg,
        "status": req.status,
        "assumptions": req.assumptions,
        "actual_result": None,
        "created_at": now,
        "updated_at": now,
    }
    await db.interventions.insert_one(doc)
    return InterventionResponse(**doc)


async def list_interventions(workspace_id: str, db: Any) -> List[InterventionResponse]:
    cursor = db.interventions.find({"workspace_id": workspace_id}).sort("created_at", -1)
    items = []
    async for item in cursor:
        item.pop("_id", None)
        items.append(InterventionResponse(**item))
    return items
