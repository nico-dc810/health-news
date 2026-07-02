from app.models.organization import Organization
from app.models.topic import Topic


def generate_content(
    organization: Organization,
    topic: Topic | None,
    *,
    topic_title: str | None,
    content_type: str,
    platform: str,
) -> dict:
    title = topic.title if topic else topic_title or "健康管理内容选题"
    service = organization.core_services or "健康管理服务"
    audience = organization.target_audience or "关注健康管理的人群"

    if content_type == "short_video":
        body = _short_video_script(title, service, audience)
        cover_text = title[:18]
    elif content_type == "moments":
        body = _moments_copy(title, service, audience)
        cover_text = "今日健康提醒"
    else:
        body = _xiaohongshu_note(title, service, audience)
        cover_text = title[:16]

    return {
        "title": title,
        "cover_text": cover_text,
        "body": body,
        "platform": platform,
        "content_type": content_type,
        "used_materials": [],
        "style_notes": "专业、克制、有温度，避免疗效承诺和绝对化表达。",
    }


def _xiaohongshu_note(title: str, service: str, audience: str) -> str:
    return (
        f"{title}\n\n"
        f"很多{audience}遇到身体状态波动时，第一反应是先忍一忍，或者在网上找一个快速方法。\n\n"
        "但从健康管理的角度看，真正重要的不是马上下结论，而是先把生活习惯、身体感受和长期困扰梳理清楚。\n\n"
        f"如果你正在关注{service}，可以先记录最近一周的睡眠、饮食、精神状态和主要不适时间点，再和专业人员沟通。\n\n"
        "日常调理不是追求立刻改变，而是找到更适合自己的调整方向。需要的话，可以先从一份简单的状态记录开始。"
    )


def _short_video_script(title: str, service: str, audience: str) -> str:
    return (
        f"开头：{title}\n\n"
        f"很多{audience}不是不重视健康，而是不知道问题到底卡在哪里。\n\n"
        "中段：如果只看单个感受，很容易误判。更稳妥的方式，是把睡眠、饮食、情绪、作息和长期习惯放在一起看。\n\n"
        f"专业建议：在了解{service}前，先完成一次基础情况梳理，明确适不适合、从哪里开始。\n\n"
        "结尾：如果你也有类似困扰，可以先把最近一周的状态记录下来，再做进一步咨询。"
    )


def _moments_copy(title: str, service: str, audience: str) -> str:
    return (
        f"{title}\n\n"
        f"最近遇到不少{audience}，真正困扰他们的不是单一问题，而是长期积累下来的状态不稳定。\n\n"
        f"做{service}，我更建议先慢下来，把问题讲清楚，再决定怎么调整。\n\n"
        "身体的变化通常不是一天形成的，管理也需要一点耐心。"
    )
