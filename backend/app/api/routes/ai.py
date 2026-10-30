from typing import Any
from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_workspace_id, get_db_dep
from app.schemas.ai import AiChatRequest, AiChatResponse
from app.services.ai_assistant_service import AiAssistantService

router = APIRouter(prefix="/ai", tags=["AI Sustainability Advisors"])


@router.post("/electricity", response_model=AiChatResponse)
async def query_electricity_assistant(
    req: AiChatRequest,
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> AiChatResponse:
    """Answers energy-related inquiries using actual workspace electricity records and calculations."""
    return await AiAssistantService.query_electricity_advisor(req.question, workspace_id, db)


@router.post("/transportation", response_model=AiChatResponse)
async def query_transportation_assistant(
    req: AiChatRequest,
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> AiChatResponse:
    """Answers transportation inquiries using bus routes, student occupancy, and fleet logs."""
    return await AiAssistantService.query_transportation_advisor(req.question, workspace_id, db)


@router.post("/waste", response_model=AiChatResponse)
async def query_waste_assistant(
    req: AiChatRequest,
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> AiChatResponse:
    """Answers waste management and recycling inquiries using recorded streams."""
    return await AiAssistantService.query_waste_advisor(req.question, workspace_id, db)


@router.post("/insights", response_model=AiChatResponse)
async def query_insights_assistant(
    req: AiChatRequest,
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> AiChatResponse:
    """
    Experience 4: Main AI Insights Assistant.
    Cross-category synthesis across Electricity, Transportation, Waste, historical trends,
    and simulated reduction scenarios. Strictly grounded in backend calculated metrics.
    """
    return await AiAssistantService.query_insights_advisor(req.question, workspace_id, db)


@router.post("/chat", response_model=AiChatResponse, include_in_schema=False)
async def query_general_chat_alias(
    req: AiChatRequest,
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> AiChatResponse:
    """Backward-compatible alias for the main cross-category AI advisor."""
    return await AiAssistantService.query_insights_advisor(req.question, workspace_id, db)
