RISK_RULES = [
    ("治愈", "疗效承诺", "避免使用治愈，可改为帮助改善体验、支持状态调整等克制表达"),
    ("根治", "疗效承诺", "避免使用根治，可改为长期管理、持续观察"),
    ("保证", "绝对化表达", "避免承诺确定结果，可改为尽量帮助、建议评估后制定方案"),
    ("永久", "绝对化表达", "避免永久、彻底等绝对化词语"),
    ("7 天见效", "明确时间效果承诺", "避免绑定具体时间和效果，可改为一段时间后观察变化"),
    ("7天见效", "明确时间效果承诺", "避免绑定具体时间和效果，可改为一段时间后观察变化"),
    ("彻底改善", "夸大宣传", "改为逐步调整、状态有所变化"),
    ("失眠", "疾病治疗暗示", "如非医疗诊疗场景，建议改为睡眠状态不佳、睡眠困扰"),
    ("加微信", "导流风险", "注意平台导流规则，建议改为私信了解"),
]


def review_content(text: str) -> dict:
    risk_items = []
    rewritten = text
    for keyword, risk_type, suggestion in RISK_RULES:
        if keyword in text:
            risk_items.append(
                {
                    "text": keyword,
                    "risk_type": risk_type,
                    "reason": f"内容包含“{keyword}”，可能触发{risk_type}风险。",
                    "suggestion": suggestion,
                }
            )
            rewritten = rewritten.replace(keyword, _safe_replacement(keyword))

    risk_level = "high" if len(risk_items) >= 3 else "medium" if risk_items else "low"
    return {
        "risk_level": risk_level,
        "risk_items": risk_items,
        "suggestions": [item["suggestion"] for item in risk_items],
        "rewritten_content": rewritten,
        "need_human_review": risk_level != "low",
    }


def _safe_replacement(keyword: str) -> str:
    replacements = {
        "治愈": "帮助改善体验",
        "根治": "长期管理",
        "保证": "尽量帮助",
        "永久": "长期",
        "7 天见效": "一段时间后观察变化",
        "7天见效": "一段时间后观察变化",
        "彻底改善": "逐步调整",
        "失眠": "睡眠状态不佳",
        "加微信": "私信了解",
    }
    return replacements.get(keyword, keyword)
