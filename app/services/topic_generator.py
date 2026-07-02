from app.models.material import Material
from app.models.organization import Organization


def generate_topics(
    organization: Organization,
    materials: list[Material],
    *,
    platform: str,
    conversion_goal: str,
    count: int,
) -> dict:
    material_tags = _collect_tags(materials)
    audience = organization.target_audience or "关注健康管理的潜在客户"
    service = organization.core_services or "健康管理服务"

    candidates = []
    for index, tag in enumerate(material_tags[:count]):
        candidates.append(
            {
                "title": f"{audience}常见的{tag}困扰，应该先从哪些日常细节看起？",
                "topic_type": "痛点科普",
                "target_audience": audience,
                "pain_point": tag,
                "platform": platform,
                "conversion_goal": conversion_goal,
                "risk_level": "low",
                "priority": 90 - index,
                "reason": f"结合机构服务：{service}，适合做温和科普和咨询引导。",
            }
        )

    backup_topics = [
        ("睡眠不好时，为什么不建议一上来就找偏方？", "睡眠管理"),
        ("总觉得累，可能需要先梳理这 4 个生活习惯", "疲劳管理"),
        ("体重管理前，先看懂自己的作息和饮食节奏", "体重管理"),
        ("亚健康调理，真正重要的是长期记录和阶段复盘", "亚健康管理"),
        ("到店咨询前，可以先准备哪些身体状态记录？", "咨询转化"),
    ]
    while len(candidates) < count:
        title, pain_point = backup_topics[len(candidates) % len(backup_topics)]
        candidates.append(
            {
                "title": title,
                "topic_type": "基础科普",
                "target_audience": audience,
                "pain_point": pain_point,
                "platform": platform,
                "conversion_goal": conversion_goal,
                "risk_level": "low",
                "priority": 70,
                "reason": f"机构资料不足时的稳健选题，可承接 {service} 的咨询场景。",
            }
        )

    return {"topics": candidates[:count]}


def _collect_tags(materials: list[Material]) -> list[str]:
    tags: list[str] = []
    for material in materials:
        for tag in material.tags or []:
            if tag not in tags:
                tags.append(tag)
    return tags or ["睡眠", "疲劳", "体重管理", "情绪压力", "日常养生"]
