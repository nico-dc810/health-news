import json
import re

from app.models.model_config import ModelConfig
from app.services.llm_gateway import chat_completion


def analyze_material_with_llm(config: ModelConfig, *, text: str, material_type: str) -> dict:
    content = chat_completion(
        config,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是大健康内容增长系统的素材拆解专家。"
                    "请只输出 JSON，不要输出 Markdown。"
                ),
            },
            {
                "role": "user",
                "content": (
                    "请把以下素材拆解为可用于内容生产的结构化资产。\n"
                    f"素材类型：{material_type}\n"
                    f"素材正文：{text}\n\n"
                    "JSON 字段必须包含：summary, material_type, audiences, pain_points, "
                    "scenes, methods, quotes, topics, risk_points, tags, risk_level。"
                ),
            },
        ],
    )
    return _json_from_text(content)


def generate_topics_with_llm(
    config: ModelConfig,
    *,
    organization_name: str,
    target_audience: str,
    core_services: str,
    material_summaries: list[str],
    platform: str,
    conversion_goal: str,
    count: int,
) -> dict:
    content = chat_completion(
        config,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是大健康机构的选题策略专家。"
                    "选题必须合规、具体、有平台感，并能服务线索转化。"
                    "请只输出 JSON，不要输出 Markdown。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"机构：{organization_name}\n"
                    f"目标客户：{target_audience}\n"
                    f"核心服务：{core_services}\n"
                    f"素材摘要：{json.dumps(material_summaries, ensure_ascii=False)}\n"
                    f"平台：{platform}\n"
                    f"转化目标：{conversion_goal}\n"
                    f"数量：{count}\n\n"
                    "请输出 JSON：{\"topics\":[...]}\n"
                    "每个 topic 包含 title, topic_type, target_audience, pain_point, "
                    "platform, conversion_goal, risk_level, priority, reason。"
                ),
            },
        ],
    )
    return _json_from_text(content)


def review_compliance_with_llm(config: ModelConfig, *, text: str) -> dict:
    content = chat_completion(
        config,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是大健康内容合规审核专家。请识别疗效承诺、绝对化表达、"
                    "疾病治疗暗示、夸大宣传、隐私泄露、违规导流等风险。"
                    "请只输出 JSON，不要输出 Markdown。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"待审核内容：{text}\n\n"
                    "请输出 JSON 字段：risk_level, risk_items, suggestions, "
                    "rewritten_content, need_human_review。risk_items 每项包含 text, "
                    "risk_type, reason, suggestion。"
                ),
            },
        ],
    )
    return _json_from_text(content)


def _json_from_text(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.S)
        if not match:
            raise ValueError("模型输出不是可解析 JSON")
        return json.loads(match.group(0))

