from sqlalchemy.orm import Session

from app.models.agent_run import AgentRun


def log_agent_run(
    db: Session,
    *,
    agent_name: str,
    workspace_id: str | None,
    organization_id: str | None,
    user_id: str | None = None,
    input_payload: dict | None = None,
    retrieved_materials: list | None = None,
    output_payload: dict | None = None,
    status: str = "success",
    error_message: str | None = None,
) -> AgentRun:
    run = AgentRun(
        agent_name=agent_name,
        workspace_id=workspace_id,
        organization_id=organization_id,
        user_id=user_id,
        input=input_payload,
        retrieved_materials=retrieved_materials,
        output=output_payload,
        status=status,
        error_message=error_message,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run

