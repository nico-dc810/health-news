from fastapi import APIRouter

from app.api.v1 import (
    agents,
    auth,
    compliance,
    content_tasks,
    knowledge,
    materials,
    model_configs,
    organizations,
    topics,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(agents.router, tags=["agents"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(materials.router, tags=["materials"])
api_router.include_router(topics.router, tags=["topics"])
api_router.include_router(content_tasks.router, tags=["content-tasks"])
api_router.include_router(compliance.router, prefix="/compliance", tags=["compliance"])
api_router.include_router(knowledge.router, tags=["knowledge"])
api_router.include_router(model_configs.router, tags=["model-configs"])
