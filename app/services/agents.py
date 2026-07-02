from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.api.v1.compliance import create_compliance_review
from app.api.v1.content_tasks import generate_content_task
from app.api.v1.knowledge import crawl_knowledge_source
from app.api.v1.materials import analyze_material
from app.api.v1.topics import generate_organization_topics
from app.schemas.agents import (
    AgentDispatchRequest,
    AgentDispatchResponse,
    AgentInfo,
    AgentPlanExecuteRequest,
    AgentPlanRequest,
    AgentPlanResponse,
    AgentPlanStep,
)
from app.schemas.compliance import ComplianceReviewRead, ComplianceReviewRequest
from app.schemas.content_task import ContentGenerateRequest, ContentTaskRead
from app.schemas.material import MaterialAnalyzeResponse
from app.schemas.topic import TopicGenerateRequest, TopicRead
from app.services.agent_logger import log_agent_run


AgentHandler = Callable[[Session, AgentDispatchRequest, list[dict[str, Any]]], Any]


@dataclass(frozen=True)
class ModuleAgent:
    name: str
    module: str
    description: str
    trigger_examples: tuple[str, ...]
    required_context: tuple[str, ...]
    can_call_agents: tuple[str, ...]
    handler: AgentHandler

    def info(self) -> AgentInfo:
        return AgentInfo(
            name=self.name,
            module=self.module,
            description=self.description,
            trigger_examples=list(self.trigger_examples),
            required_context=list(self.required_context),
            can_call_agents=list(self.can_call_agents),
        )


INTENT_DEFINITIONS = {
    "write_content": {
        "label": "生成合规内容",
        "primary_agent": "content_producer",
        "required_inputs": ["organization", "topic_or_material", "platform", "content_type"],
        "sub_agents": ["material_analyzer", "compliance_reviewer"],
        "reason": "用户希望产出可发布内容，需要理解素材或主题，再生成草稿并完成合规检查。",
    },
    "generate_topics": {
        "label": "规划合规选题",
        "primary_agent": "topic_strategy",
        "required_inputs": ["organization", "platform", "conversion_goal", "count"],
        "sub_agents": ["material_analyzer"],
        "reason": "用户希望获得内容选题，需要结合机构定位、素材资产、平台和转化目标生成候选方向。",
    },
    "review_compliance": {
        "label": "检查内容合规",
        "primary_agent": "compliance_reviewer",
        "required_inputs": ["organization", "input_text"],
        "sub_agents": [],
        "reason": "用户希望判断文案风险，只需要合规审核 Agent 识别风险并给出改写建议。",
    },
    "analyze_material": {
        "label": "拆解素材资产",
        "primary_agent": "material_analyzer",
        "required_inputs": ["material"],
        "sub_agents": [],
        "reason": "用户希望把原始素材变成可复用资产，需要拆解标签、人群、痛点、场景和风险点。",
    },
    "crawl_knowledge": {
        "label": "采集知识源",
        "primary_agent": "knowledge_crawler",
        "required_inputs": ["source"],
        "sub_agents": ["material_analyzer", "compliance_reviewer"],
        "reason": "用户希望沉淀外部知识，需要采集知识源并做基础结构化与风险识别。",
    },
}


def list_agents() -> list[AgentInfo]:
    return [agent.info() for agent in AGENTS.values()]


def create_agent_plan(payload: AgentPlanRequest) -> AgentPlanResponse:
    intent = detect_intent(payload.problem, payload.context)
    definition = INTENT_DEFINITIONS[intent]
    steps = _build_plan_steps(intent, payload.context)
    return AgentPlanResponse(
        intent=intent,
        intent_label=definition["label"],
        primary_agent=definition["primary_agent"],
        required_inputs=definition["required_inputs"],
        sub_agents=[step.agent_name for step in steps if step.agent_name != definition["primary_agent"]],
        reason=definition["reason"],
        steps=steps,
        context=_normalize_context(intent, payload.context),
    )


def execute_agent_plan(db: Session, payload: AgentPlanExecuteRequest) -> AgentDispatchResponse:
    plan = payload.plan
    context = {**payload.context, **plan.context, "intent": plan.intent}
    trace: list[dict[str, Any]] = [
        {
            "agent": "dispatcher",
            "action": "create_plan",
            "intent": plan.intent,
            "primary_agent": plan.primary_agent,
            "status": "success",
        }
    ]
    results: dict[str, Any] = {}
    final_result: Any = None

    try:
        for step in plan.steps:
            step_payload = AgentDispatchRequest(
                problem=payload.problem,
                organization_id=payload.organization_id,
                workspace_id=payload.workspace_id,
                user_id=payload.user_id,
                agent_name=step.agent_name,
                context=context,
            )
            step_trace: list[dict[str, Any]] = []
            raw_result = _run_agent(db, step_payload, step_trace)
            serialized = _serialize_result(step.agent_name, raw_result)
            results[step.agent_name] = serialized
            context[step.agent_name] = serialized
            final_result = serialized
            trace.append(
                {
                    "agent": step.agent_name,
                    "action": step.action,
                    "purpose": step.purpose,
                    "status": "success",
                }
            )

        response = AgentDispatchResponse(
            agent_name=plan.primary_agent,
            intent=plan.intent,
            status="success",
            message="plan executed",
            result={"final": final_result, "by_agent": results},
            trace=trace,
        )
        log_agent_run(
            db,
            agent_name=f"plan->{plan.primary_agent}",
            workspace_id=payload.workspace_id,
            organization_id=payload.organization_id,
            user_id=payload.user_id,
            input_payload=jsonable_encoder(payload),
            output_payload=jsonable_encoder(response),
        )
        return response
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        log_agent_run(
            db,
            agent_name=f"plan->{plan.primary_agent}",
            workspace_id=payload.workspace_id,
            organization_id=payload.organization_id,
            user_id=payload.user_id,
            input_payload=jsonable_encoder(payload),
            status="failed",
            error_message=str(exc),
        )
        raise


def dispatch_agent(db: Session, payload: AgentDispatchRequest) -> AgentDispatchResponse:
    plan = create_agent_plan(
        AgentPlanRequest(
            problem=payload.problem,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            user_id=payload.user_id,
            context=payload.context,
        )
    )
    if payload.agent_name:
        plan.primary_agent = payload.agent_name
        plan.steps = [
            AgentPlanStep(
                order=1,
                agent_name=payload.agent_name,
                action="run_agent",
                purpose="按显式指定 Agent 执行单步任务。",
            )
        ]
    return execute_agent_plan(
        db,
        AgentPlanExecuteRequest(
            problem=payload.problem,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            user_id=payload.user_id,
            context=payload.context,
            plan=plan,
        ),
    )


def detect_intent(problem: str, context: dict[str, Any]) -> str:
    intent = context.get("intent")
    if intent in INTENT_DEFINITIONS:
        return intent

    text = f"{problem} {' '.join(str(value) for value in context.values())}".lower()
    routes = [
        ("review_compliance", ("合规", "审核", "风险", "违规", "review", "risk")),
        ("analyze_material", ("素材", "拆解", "案例", "提炼", "material", "analyze")),
        ("generate_topics", ("选题", "话题", "标题", "策划", "topic", "idea")),
        ("crawl_knowledge", ("采集", "知识", "抓取", "rss", "source", "crawl")),
        ("write_content", ("写", "内容", "文案", "小红书", "脚本", "笔记", "content", "post", "article", "write")),
    ]
    for name, keywords in routes:
        if any(keyword in text for keyword in keywords):
            return name
    return "write_content"


def _build_plan_steps(intent: str, context: dict[str, Any]) -> list[AgentPlanStep]:
    steps: list[AgentPlanStep] = []
    if intent == "write_content":
        if context.get("material_id"):
            steps.append(_step(1, "material_analyzer", "analyze_material", "先拆解素材，提炼痛点、标签和风险边界。"))
            order = 2
        else:
            order = 1
        steps.append(_step(order, "content_producer", "generate_content", "生成适合平台的内容草稿。"))
        steps.append(_step(order + 1, "compliance_reviewer", "review_content", "对生成文案做合规检查和改写建议。"))
    elif intent == "generate_topics":
        if context.get("material_id"):
            steps.append(_step(1, "material_analyzer", "analyze_material", "先把素材拆成可复用资产。"))
            order = 2
        else:
            order = 1
        steps.append(_step(order, "topic_strategy", "generate_topics", "结合机构定位、平台和目标生成选题。"))
    elif intent == "review_compliance":
        steps.append(_step(1, "compliance_reviewer", "review_content", "识别风险表达并给出合规改写。"))
    elif intent == "analyze_material":
        steps.append(_step(1, "material_analyzer", "analyze_material", "拆解素材为标签、痛点、场景和风险点。"))
    elif intent == "crawl_knowledge":
        steps.append(_step(1, "knowledge_crawler", "crawl_source", "采集知识源并沉淀知识卡片。"))
    return steps


def _step(order: int, agent_name: str, action: str, purpose: str) -> AgentPlanStep:
    return AgentPlanStep(order=order, agent_name=agent_name, action=action, purpose=purpose)


def _normalize_context(intent: str, context: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(context)
    normalized["intent"] = intent
    return normalized


def _run_agent(db: Session, payload: AgentDispatchRequest, trace: list[dict[str, Any]]) -> Any:
    agent_name = payload.agent_name or INTENT_DEFINITIONS[detect_intent(payload.problem, payload.context)]["primary_agent"]
    agent = AGENTS.get(agent_name)
    if not agent:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {agent_name}")
    return agent.handler(db, payload, trace)


def _serialize_result(agent_name: str, result: Any) -> Any:
    if agent_name == "topic_strategy":
        return [TopicRead.model_validate(item).model_dump(mode="json") for item in result]
    if agent_name == "content_producer":
        return ContentTaskRead.model_validate(result).model_dump(mode="json")
    if agent_name == "material_analyzer":
        return MaterialAnalyzeResponse.model_validate(result).model_dump(mode="json")
    if agent_name == "compliance_reviewer":
        return ComplianceReviewRead.model_validate(result).model_dump(mode="json")
    return jsonable_encoder(result)


def _require(payload: AgentDispatchRequest, key: str) -> Any:
    value = payload.context.get(key)
    if value is None:
        raise HTTPException(status_code=422, detail=f"context.{key} is required")
    return value


def _organization_id(payload: AgentDispatchRequest) -> str:
    organization_id = payload.organization_id or payload.context.get("organization_id")
    if not organization_id:
        raise HTTPException(status_code=422, detail="organization_id is required")
    return organization_id


def _topic_strategy_agent(db: Session, payload: AgentDispatchRequest, trace: list[dict[str, Any]]) -> Any:
    organization_id = _organization_id(payload)
    request = TopicGenerateRequest(
        organization_id=organization_id,
        ip_profile_id=payload.context.get("ip_profile_id"),
        platform=payload.context.get("platform", "xiaohongshu"),
        conversion_goal=payload.context.get("conversion_goal", "lead_consultation"),
        count=int(payload.context.get("count", 5)),
    )
    trace.append({"agent": "topic_strategy", "action": "generate_topics", "input": request.model_dump()})
    return generate_organization_topics(organization_id, request, db)


def _content_producer_agent(db: Session, payload: AgentDispatchRequest, trace: list[dict[str, Any]]) -> Any:
    organization_id = _organization_id(payload)
    request = ContentGenerateRequest(
        organization_id=organization_id,
        ip_profile_id=payload.context.get("ip_profile_id"),
        topic_id=payload.context.get("topic_id"),
        topic_title=payload.context.get("topic_title") or payload.problem,
        content_type=payload.context.get("content_type", "note"),
        platform=payload.context.get("platform", "xiaohongshu"),
    )
    trace.append({"agent": "content_producer", "action": "generate_content", "input": request.model_dump()})
    return generate_content_task(request, db)


def _compliance_reviewer_agent(db: Session, payload: AgentDispatchRequest, trace: list[dict[str, Any]]) -> Any:
    organization_id = _organization_id(payload)
    input_text = payload.context.get("input_text") or _content_text_from_context(payload.context) or payload.problem
    request = ComplianceReviewRequest(
        organization_id=organization_id,
        content_task_id=payload.context.get("content_task_id"),
        input_text=input_text,
    )
    trace.append({"agent": "compliance_reviewer", "action": "review_content", "input": request.model_dump()})
    return create_compliance_review(request, db)


def _content_text_from_context(context: dict[str, Any]) -> str | None:
    content_result = context.get("content_producer")
    if isinstance(content_result, dict):
        return content_result.get("body")
    return None


def _material_analyzer_agent(db: Session, payload: AgentDispatchRequest, trace: list[dict[str, Any]]) -> Any:
    material_id = _require(payload, "material_id")
    trace.append({"agent": "material_analyzer", "action": "analyze_material", "material_id": material_id})
    return analyze_material(material_id, db)


def _knowledge_crawler_agent(db: Session, payload: AgentDispatchRequest, trace: list[dict[str, Any]]) -> Any:
    source_id = _require(payload, "source_id")
    trace.append({"agent": "knowledge_crawler", "action": "crawl_source", "source_id": source_id})
    return crawl_knowledge_source(source_id, db)


AGENTS: dict[str, ModuleAgent] = {
    "material_analyzer": ModuleAgent(
        name="material_analyzer",
        module="materials",
        description="拆解素材，提炼标签、痛点、可复用内容资产和风险点。",
        trigger_examples=("拆解这条素材", "分析客户案例", "提炼素材卖点"),
        required_context=("material_id",),
        can_call_agents=("compliance_reviewer",),
        handler=_material_analyzer_agent,
    ),
    "topic_strategy": ModuleAgent(
        name="topic_strategy",
        module="topics",
        description="基于机构定位、素材和目标平台生成合规选题。",
        trigger_examples=("帮我做选题", "生成 5 个小红书话题", "策划内容标题"),
        required_context=("organization_id",),
        can_call_agents=("material_analyzer",),
        handler=_topic_strategy_agent,
    ),
    "content_producer": ModuleAgent(
        name="content_producer",
        module="content_tasks",
        description="生成内容草稿，并把结果交给合规审核 Agent。",
        trigger_examples=("写一篇小红书", "生成内容", "写短视频脚本"),
        required_context=("organization_id",),
        can_call_agents=("topic_strategy", "compliance_reviewer"),
        handler=_content_producer_agent,
    ),
    "compliance_reviewer": ModuleAgent(
        name="compliance_reviewer",
        module="compliance",
        description="审核大健康内容合规风险，并给出改写建议。",
        trigger_examples=("检查风险", "这段话违规吗", "做合规审核"),
        required_context=("organization_id", "input_text"),
        can_call_agents=(),
        handler=_compliance_reviewer_agent,
    ),
    "knowledge_crawler": ModuleAgent(
        name="knowledge_crawler",
        module="knowledge",
        description="采集知识源并沉淀为知识卡片。",
        trigger_examples=("采集知识库", "抓取这个 RSS", "同步公开资讯"),
        required_context=("source_id",),
        can_call_agents=("material_analyzer", "compliance_reviewer"),
        handler=_knowledge_crawler_agent,
    ),
}
