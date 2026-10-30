from fastapi import APIRouter
from app.api.routes.ai import router as ai_router
from app.api.routes.auth import router as auth_router
from app.api.routes.bus_routes import router as bus_routes_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.demo import router as demo_router
from app.api.routes.electricity import router as electricity_router
from app.api.routes.emissions import router as emissions_router
from app.api.routes.progress import router as progress_router
from app.api.routes.reports import router as reports_router
from app.api.routes.simulator import router as simulator_router
from app.api.routes.transportation import router as transportation_router
from app.api.routes.waste import router as waste_router

api_router = APIRouter(prefix="/api")

# Register domain routers under /api
api_router.include_router(auth_router)
api_router.include_router(electricity_router)
api_router.include_router(bus_routes_router)
api_router.include_router(transportation_router)
api_router.include_router(waste_router)
api_router.include_router(emissions_router)
api_router.include_router(dashboard_router)
api_router.include_router(ai_router)
api_router.include_router(simulator_router)
api_router.include_router(progress_router)
api_router.include_router(reports_router)
api_router.include_router(demo_router)
