from collections import Counter
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeItem, KnowledgeSource
from app.services.knowledge_crawler import analyze_knowledge_entry, crawl_source


@dataclass(frozen=True)
class SourcePreset:
    name: str
    source_type: str
    url: str
    category: str
    credibility_level: str = "medium"
    crawl_frequency: str = "daily"


SOURCE_PRESETS = (
    SourcePreset(
        name="本地演示资讯样例",
        source_type="website",
        url="http://127.0.0.1:8000/demo/sample_health_news.html",
        category="国内大健康",
        credibility_level="medium",
    ),
    SourcePreset(
        name="国家市场监督管理总局",
        source_type="website",
        url="https://www.samr.gov.cn/",
        category="政策法规",
        credibility_level="high",
    ),
    SourcePreset(
        name="国家卫生健康委员会",
        source_type="website",
        url="https://www.nhc.gov.cn/",
        category="政策法规",
        credibility_level="high",
    ),
    SourcePreset(
        name="人民网健康",
        source_type="website",
        url="http://health.people.com.cn/",
        category="国内大健康",
    ),
    SourcePreset(
        name="新华网健康",
        source_type="website",
        url="http://www.news.cn/health/",
        category="国内大健康",
    ),
    SourcePreset(
        name="NutraIngredients",
        source_type="website",
        url="https://www.nutraingredients.com/",
        category="全球大健康",
    ),
    SourcePreset(
        name="Direct Selling News",
        source_type="website",
        url="https://www.directsellingnews.com/",
        category="全球直销",
    ),
    SourcePreset(
        name="Business For Home",
        source_type="website",
        url="https://www.businessforhome.org/",
        category="全球直销",
        credibility_level="high",
    ),
    SourcePreset(
        name="DSEF 直销教育基金会",
        source_type="website",
        url="https://www.dsef.org/",
        category="行业研究",
        credibility_level="high",
    ),
    SourcePreset(
        name="MLM Legal",
        source_type="website",
        url="https://www.mlmlegal.com/",
        category="合规研究",
        credibility_level="high",
    ),
    SourcePreset(
        name="Network Marketing Pro",
        source_type="website",
        url="https://networkmarketingpro.com/",
        category="教育培训",
    ),
    SourcePreset(
        name="Social Selling News",
        source_type="website",
        url="https://socialsellingnews.com/",
        category="全球直销",
        credibility_level="high",
    ),
    SourcePreset(
        name="直销快评网",
        source_type="website",
        url="https://www.dskuaiping.com/",
        category="国内直销",
    ),
    SourcePreset(
        name="直销博客网",
        source_type="website",
        url="http://www.dsblog.net/",
        category="国内直销",
    ),
    SourcePreset(
        name="中直网",
        source_type="website",
        url="http://www.zhixiaowang.com/",
        category="国内直销",
    ),
    SourcePreset(
        name="道道网",
        source_type="website",
        url="http://www.dsdod.com/",
        category="国内直销",
    ),
    SourcePreset(
        name="直销行业网",
        source_type="website",
        url="http://www.dsichn.com/",
        category="国内直销",
    ),
    SourcePreset(
        name="直销报道网",
        source_type="website",
        url="http://www.chndsnews.com/",
        category="国内直销",
    ),
    SourcePreset(
        name="当代直销网",
        source_type="website",
        url="https://www.dmtoday.cn/",
        category="国内直销",
    ),
    SourcePreset(
        name="直销专业网",
        source_type="website",
        url="http://www.cdsp.com.cn/",
        category="国内直销",
    ),
    SourcePreset(
        name="直销堂网",
        source_type="website",
        url="http://www.cdsp.com.cn/",
        category="国内直销",
    ),
    SourcePreset(
        name="新商业头条网",
        source_type="website",
        url="http://www.nbtt319.com/",
        category="国内直销",
    ),
    SourcePreset(
        name="易直销网",
        source_type="website",
        url="https://www.ezhixiao.com.cn/",
        category="国内直销",
    ),
    SourcePreset(
        name="DSC 直销资讯",
        source_type="website",
        url="https://www.cndsc.com/?action-viewnews-itemid-43269",
        category="国内直销",
    ),
    SourcePreset(
        name="直销100网",
        source_type="website",
        url="http://zhixiao100.com.cn/",
        category="国内直销",
    ),
)


REPOSITORY_OPTIONS = [
    {
        "id": "local_sqlite",
        "name": "本地数据库",
        "role": "系统主库",
        "suitable_for": ["抓取任务", "去重", "状态记录", "看板统计", "Agent 调用"],
        "limitations": ["需要部署服务才能多人访问"],
        "recommended_use": "第一阶段默认使用，保证抓取链路、去重和任务状态稳定。",
        "status": "ready",
    },
    {
        "id": "notion",
        "name": "Notion",
        "role": "外部知识库/展示库",
        "suitable_for": ["老板查看", "资料归档", "人工编辑", "项目协作"],
        "limitations": ["不适合高频抓取写入", "权限和 API 配置需要单独授权"],
        "recommended_use": "作为精选内参、行业简报和人工维护知识库的同步目标。",
        "status": "adapter_planned",
    },
    {
        "id": "feishu",
        "name": "飞书",
        "role": "团队协作知识库",
        "suitable_for": ["团队文档", "审批协作", "通知提醒", "内参分发"],
        "limitations": ["开放能力取决于企业权限", "需要应用凭证和文档空间配置"],
        "recommended_use": "适合把每日内参、风险提醒和任务通知推给团队。",
        "status": "adapter_planned",
    },
    {
        "id": "getnote",
        "name": "Get笔记",
        "role": "个人/团队资料沉淀",
        "suitable_for": ["资料收藏", "语义搜索", "知识沉淀", "人工补充"],
        "limitations": ["更适合知识沉淀，不适合承担抓取任务调度主库"],
        "recommended_use": "适合把精选资讯、案例和研报沉淀为可搜索笔记。",
        "status": "adapter_planned",
    },
    {
        "id": "ima",
        "name": "ima 知识库",
        "role": "外部知识查询入口",
        "suitable_for": ["个人知识管理", "资料问答", "知识检索"],
        "limitations": ["需要确认可用 API 或自动化接入方式"],
        "recommended_use": "先作为候选外部知识库，不作为 MVP 主库。",
        "status": "needs_research",
    },
]


def seed_intelligence_sources(
    db: Session,
    *,
    workspace_id: str,
    organization_id: str | None = None,
    reset_existing: bool = False,
) -> list[KnowledgeSource]:
    if reset_existing:
        existing = db.scalars(
            select(KnowledgeSource).where(KnowledgeSource.workspace_id == workspace_id)
        ).all()
        for source in existing:
            db.delete(source)
        db.flush()

    created_or_existing: list[KnowledgeSource] = []
    for preset in SOURCE_PRESETS:
        source = db.scalar(
            select(KnowledgeSource).where(
                KnowledgeSource.workspace_id == workspace_id,
                KnowledgeSource.url == preset.url,
            )
        )
        if source is None:
            source = KnowledgeSource(
                workspace_id=workspace_id,
                organization_id=organization_id,
                name=preset.name,
                source_type=preset.source_type,
                url=preset.url,
                crawl_frequency=preset.crawl_frequency,
                category=preset.category,
                credibility_level=preset.credibility_level,
            )
            db.add(source)
        created_or_existing.append(source)

    db.commit()
    for source in created_or_existing:
        db.refresh(source)
    return created_or_existing


def build_intelligence_dashboard(
    db: Session,
    *,
    workspace_id: str | None = None,
    organization_id: str | None = None,
) -> dict:
    source_statement = select(KnowledgeSource)
    item_statement = select(KnowledgeItem).order_by(KnowledgeItem.crawled_at.desc())

    if workspace_id:
        source_statement = source_statement.where(KnowledgeSource.workspace_id == workspace_id)
    if organization_id:
        source_statement = source_statement.where(KnowledgeSource.organization_id == organization_id)
        item_statement = item_statement.where(KnowledgeItem.organization_id == organization_id)

    sources = list(db.scalars(source_statement))
    count_statement = select(func.count(KnowledgeItem.id))
    if organization_id:
        count_statement = count_statement.where(KnowledgeItem.organization_id == organization_id)

    latest_items = list(db.scalars(item_statement.limit(60)))
    categories = Counter(item.category or "未分类" for item in latest_items)
    high_risk_count = sum(
        1
        for item in latest_items
        if isinstance(item.compliance_risk, dict)
        and item.compliance_risk.get("risk_level") in {"high", "medium"}
    )

    return {
        "source_count": len(sources),
        "active_source_count": sum(1 for source in sources if source.status == "active"),
        "item_count": db.scalar(count_statement) or 0,
        "high_risk_count": high_risk_count,
        "latest_items": latest_items,
        "category_counts": dict(categories),
        "repository_options": REPOSITORY_OPTIONS,
    }


def crawl_active_sources(
    db: Session,
    *,
    workspace_id: str,
    organization_id: str | None = None,
    max_sources: int = 3,
) -> dict:
    statement = (
        select(KnowledgeSource)
        .where(KnowledgeSource.workspace_id == workspace_id, KnowledgeSource.status == "active")
        .order_by(KnowledgeSource.last_crawled_at.is_not(None), KnowledgeSource.updated_at.desc())
        .limit(max(1, min(max_sources, 25)))
    )
    if organization_id:
        statement = statement.where(KnowledgeSource.organization_id == organization_id)

    sources = list(db.scalars(statement))
    item_count = 0
    errors: list[str] = []

    for source in sources:
        try:
            entries = crawl_source(source.url, source.source_type)
            for entry in entries:
                existing = db.scalar(
                    select(KnowledgeItem).where(
                        KnowledgeItem.source_id == source.id,
                        KnowledgeItem.url == entry.url,
                        KnowledgeItem.title == entry.title,
                    )
                )
                if existing:
                    analysis = analyze_knowledge_entry(
                        entry,
                        category=source.category,
                        credibility_level=source.credibility_level,
                    )
                    existing.author = entry.author
                    existing.published_at = entry.published_at
                    existing.crawled_at = datetime.utcnow()
                    existing.raw_text = entry.raw_text
                    existing.summary = analysis["summary"]
                    existing.category = analysis["category"]
                    existing.tags = analysis["tags"]
                    existing.audiences = analysis["audiences"]
                    existing.pain_points = analysis["pain_points"]
                    existing.topic_suggestions = analysis["topic_suggestions"]
                    existing.compliance_risk = analysis["compliance_risk"]
                    existing.credibility_score = analysis["credibility_score"]
                    existing.status = analysis["status"]
                    item_count += 1
                    continue

                analysis = analyze_knowledge_entry(
                    entry,
                    category=source.category,
                    credibility_level=source.credibility_level,
                )
                db.add(
                    KnowledgeItem(
                        source_id=source.id,
                        organization_id=source.organization_id,
                        title=entry.title[:500],
                        url=entry.url,
                        author=entry.author,
                        published_at=entry.published_at,
                        crawled_at=datetime.utcnow(),
                        raw_text=entry.raw_text,
                        summary=analysis["summary"],
                        category=analysis["category"],
                        tags=analysis["tags"],
                        audiences=analysis["audiences"],
                        pain_points=analysis["pain_points"],
                        topic_suggestions=analysis["topic_suggestions"],
                        compliance_risk=analysis["compliance_risk"],
                        credibility_score=analysis["credibility_score"],
                        status=analysis["status"],
                    )
                )
                item_count += 1
            source.last_crawled_at = datetime.utcnow()
            db.commit()
        except ValueError as exc:
            db.rollback()
            errors.append(f"{source.name}: {exc}")

    return {
        "source_count": len(sources),
        "item_count": item_count,
        "errors": errors,
        "message": f"已处理 {len(sources)} 个来源，获得 {item_count} 条资讯",
    }
