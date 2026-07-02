from typing import Any

from pydantic import BaseModel, Field


class AgentDispatchRequest(BaseModel):
    problem: str = Field(..., min_length=1)
    organization_id: str | None = None
    workspace_id: str | None = None
    user_id: str | None = None
    agent_name: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class AgentInfo(BaseModel):
    name: str
    module: str
    description: str
    trigger_examples: list[str]
    required_context: list[str]
    can_call_agents: list[str] = Field(default_factory=list)


class AgentDispatchResponse(BaseModel):
    agent_name: str
    intent: str
    status: str
    message: str
    result: Any | None = None
    trace: list[dict[str, Any]] = Field(default_factory=list)


class AgentPlanStep(BaseModel):
    order: int
    agent_name: str
    action: str
    purpose: str
    status: str = "pending"


class AgentPlanRequest(BaseModel):
    problem: str = Field(..., min_length=1)
    organization_id: str | None = None
    workspace_id: str | None = None
    user_id: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class AgentPlanResponse(BaseModel):
    intent: str
    intent_label: str
    primary_agent: str
    required_inputs: list[str]
    sub_agents: list[str] = Field(default_factory=list)
    reason: str
    steps: list[AgentPlanStep]
    context: dict[str, Any] = Field(default_factory=dict)


class AgentPlanExecuteRequest(AgentPlanRequest):
    plan: AgentPlanResponse
