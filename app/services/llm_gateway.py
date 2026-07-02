import json
import urllib.error
import urllib.request

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.model_config import ModelConfig


def mask_api_key(api_key: str | None) -> str | None:
    if not api_key:
        return None
    if len(api_key) <= 8:
        return "****"
    return f"{api_key[:4]}****{api_key[-4:]}"


def model_config_to_read(config: ModelConfig) -> dict:
    return {
        "id": config.id,
        "created_at": config.created_at,
        "updated_at": config.updated_at,
        "workspace_id": config.workspace_id,
        "organization_id": config.organization_id,
        "name": config.name,
        "provider": config.provider,
        "api_base_url": config.api_base_url,
        "masked_api_key": mask_api_key(config.api_key),
        "model_name": config.model_name,
        "use_case": config.use_case,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "is_default": config.is_default,
        "status": config.status,
    }


def resolve_model_config(
    db: Session,
    *,
    workspace_id: str | None,
    organization_id: str | None,
    use_case: str = "default",
) -> ModelConfig | None:
    statement = select(ModelConfig).where(ModelConfig.status == "active")
    if organization_id:
        organization_match = statement.where(ModelConfig.organization_id == organization_id)
        config = db.scalar(
            organization_match.where(ModelConfig.use_case == use_case).order_by(
                ModelConfig.is_default.desc(), ModelConfig.created_at.desc()
            )
        )
        if config:
            return config
        config = db.scalar(
            organization_match.order_by(ModelConfig.is_default.desc(), ModelConfig.created_at.desc())
        )
        if config:
            return config

    if workspace_id:
        workspace_match = statement.where(ModelConfig.workspace_id == workspace_id)
        config = db.scalar(
            workspace_match.where(ModelConfig.use_case == use_case).order_by(
                ModelConfig.is_default.desc(), ModelConfig.created_at.desc()
            )
        )
        if config:
            return config
        return db.scalar(
            workspace_match.order_by(ModelConfig.is_default.desc(), ModelConfig.created_at.desc())
        )
    return None


def test_model_config(config: ModelConfig) -> dict:
    if config.provider == "mock":
        return {
            "ok": True,
            "provider": config.provider,
            "model_name": config.model_name,
            "message": "Mock model is available.",
            "sample": "模型配置已保存，当前使用 mock 模式。",
        }

    sample = chat_completion(
        config,
        messages=[
            {"role": "system", "content": "You are a concise assistant."},
            {"role": "user", "content": "回复：模型连接测试成功"},
        ],
    )
    return {
        "ok": True,
        "provider": config.provider,
        "model_name": config.model_name,
        "message": "Model connection succeeded.",
        "sample": sample,
    }


def chat_completion(config: ModelConfig, *, messages: list[dict]) -> str:
    if config.provider == "mock":
        return _mock_response(messages)

    if not config.api_key:
        raise ValueError("模型 API Key 不能为空")
    if not config.api_base_url:
        raise ValueError("模型 API Base URL 不能为空")

    endpoint = config.api_base_url.rstrip("/")
    if not endpoint.endswith("/chat/completions"):
        endpoint = f"{endpoint}/chat/completions"

    payload = {
        "model": config.model_name,
        "messages": messages,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"模型接口返回错误：{exc.code} {body[:300]}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"无法连接模型接口：{exc}") from exc

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("模型接口返回格式无法识别") from exc


def _mock_response(messages: list[dict]) -> str:
    user_message = next((item["content"] for item in reversed(messages) if item["role"] == "user"), "")
    return f"[mock] 已收到请求：{user_message[:80]}"

