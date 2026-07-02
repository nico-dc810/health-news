from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.agents import (
    AgentDispatchRequest,
    AgentDispatchResponse,
    AgentInfo,
    AgentPlanExecuteRequest,
    AgentPlanRequest,
    AgentPlanResponse,
)
from app.services.agents import create_agent_plan, dispatch_agent, execute_agent_plan, list_agents

router = APIRouter()


@router.get("/agents", response_model=list[AgentInfo])
def get_agents() -> list[AgentInfo]:
    return list_agents()


@router.post("/agents/dispatch", response_model=AgentDispatchResponse)
def dispatch_agent_request(
    payload: AgentDispatchRequest,
    db: Session = Depends(get_db),
) -> AgentDispatchResponse:
    return dispatch_agent(db, payload)


@router.post("/agents/plan", response_model=AgentPlanResponse)
def create_agent_plan_request(payload: AgentPlanRequest) -> AgentPlanResponse:
    return create_agent_plan(payload)


@router.post("/agents/execute", response_model=AgentDispatchResponse)
def execute_agent_plan_request(
    payload: AgentPlanExecuteRequest,
    db: Session = Depends(get_db),
) -> AgentDispatchResponse:
    return execute_agent_plan(db, payload)
