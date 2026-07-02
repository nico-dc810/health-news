KEYWORD_TAGS = {
    "睡眠": ["睡眠", "睡不", "睡得", "失眠", "入睡", "早醒"],
    "疲劳": ["疲劳", "累", "没精神", "乏力"],
    "体重管理": ["体重", "减重", "肥胖", "身材"],
    "情绪压力": ["焦虑", "情绪", "压力", "烦躁"],
    "产后": ["产后", "宝妈", "妈妈"],
    "政策监管": ["监管", "政策", "法规", "市场监督", "卫健委", "医保", "广告法"],
    "营养健康": ["营养", "膳食", "保健食品", "功能食品", "益生菌", "维生素"],
    "中医养生": ["中医", "养生", "调理", "节气", "经络", "药膳"],
    "健康产业": ["大健康", "健康产业", "医疗健康", "康养", "健康中国"],
    "直销零售": ["直销", "新零售", "私域", "社交零售", "代理", "经销商"],
    "AI数字化": ["AI", "人工智能", "数字化", "智能", "数据", "数智"],
}


def analyze_material_text(text: str | None, material_type: str) -> dict:
    content = text or ""
    tags = [
        tag
        for tag, keywords in KEYWORD_TAGS.items()
        if any(keyword in content for keyword in keywords)
    ]
    risk_points = []
    if any(word in content for word in ["治愈", "根治", "保证", "7 天见效", "7天见效", "彻底改善"]):
        risk_points.append("素材中可能存在疗效承诺或绝对化表达，生成内容时需要弱化。")
    if "失眠" in content:
        risk_points.append("“失眠”容易形成疾病治疗暗示，建议改为“睡眠状态不佳”。")

    summary = _summarize_content(content)
    return {
        "summary": summary,
        "material_type": material_type,
        "audiences": _guess_audiences(content),
        "pain_points": tags or ["健康管理需求"],
        "scenes": _guess_scenes(content),
        "methods": _guess_methods(content),
        "quotes": _extract_quotes(content),
        "topics": _suggest_topics(tags),
        "risk_points": risk_points,
        "tags": tags,
        "risk_level": "medium" if risk_points else "low",
    }


def split_chunks(text: str | None, chunk_size: int = 500) -> list[str]:
    content = (text or "").strip()
    if not content:
        return []
    return [content[index : index + chunk_size] for index in range(0, len(content), chunk_size)]


def _guess_audiences(content: str) -> list[str]:
    if "产后" in content or "宝妈" in content or "妈妈" in content:
        return ["产后女性"]
    if "42 岁" in content or "女性" in content:
        return ["35-50 岁关注状态管理的女性"]
    if "中老年" in content:
        return ["中老年人群"]
    return ["关注健康管理的人群"]


def _guess_scenes(content: str) -> list[str]:
    scenes = []
    if "门店" in content or "到店" in content:
        scenes.append("门店咨询")
    if "小红书" in content:
        scenes.append("小红书科普")
    if "记录" in content or "评估" in content:
        scenes.append("咨询前状态梳理")
    return scenes or ["内容科普", "私域咨询"]


def _guess_methods(content: str) -> list[str]:
    methods = []
    if "记录" in content:
        methods.append("记录一周睡眠、饮食和情绪变化")
    if "评估" in content:
        methods.append("先做基础评估，再决定调理方向")
    return methods or ["先梳理生活习惯，再给出个性化建议"]


def _extract_quotes(content: str) -> list[str]:
    if not content:
        return []
    return [content[:80]]


def _suggest_topics(tags: list[str]) -> list[str]:
    if not tags:
        return ["这条资讯对大健康机构有什么运营启发？"]
    return [f"围绕{tag}，大健康机构可以提炼哪些合规内容选题？" for tag in tags[:5]]


def _summarize_content(content: str) -> str:
    cleaned = _clean_noise(" ".join(content.split()))
    if not cleaned:
        return "暂无素材正文"

    sentences = _split_sentences(cleaned)
    if not sentences:
        return f"精华内容：{cleaned[:220]}\n我的思考：这条信息需要结合来源可信度和业务场景进一步判断，避免只做资讯搬运。"

    useful = _pick_core_sentences(sentences, limit=4)
    essence = "；".join(useful)[:420] if useful else cleaned[:260]
    thinking = _build_thinking(cleaned)
    return f"精华内容：{essence}\n我的思考：{thinking}"


def _split_sentences(content: str) -> list[str]:
    normalized = content
    for mark in ["！", "？", "!", "?"]:
        normalized = normalized.replace(mark, "。")
    return [part.strip(" ，,;；") for part in normalized.split("。") if part.strip()]


def _pick_core_sentences(sentences: list[str], *, limit: int) -> list[str]:
    score_words = [
        "发布",
        "指出",
        "显示",
        "增长",
        "监管",
        "政策",
        "产业",
        "市场",
        "趋势",
        "健康",
        "营养",
        "风险",
        "企业",
        "用户",
        "消费者",
        "数字化",
    ]
    skip_words = ["首页", "登录", "注册", "联系我们", "版权所有", "广告", "免责声明", "上一篇", "下一篇", "慈善积分榜", "获牌企业"]
    candidates = []
    leading = []
    seen = set()
    for index, sentence in enumerate(sentences):
        if len(sentence) < 16 or len(sentence) > 260:
            continue
        if any(word in sentence for word in skip_words):
            continue
        key = sentence[:40]
        if key in seen:
            continue
        seen.add(key)
        if index < 6 and len(leading) < 2:
            leading.append(sentence)
        score = sum(2 for word in score_words if word in sentence)
        if index < 8:
            score += 3
        score += min(len(sentence), 160) / 80
        candidates.append((score, sentence))
    candidates.sort(key=lambda item: item[0], reverse=True)
    picked = list(leading)
    for _, sentence in candidates:
        if sentence not in picked:
            picked.append(sentence)
        if len(picked) >= limit:
            break
    if picked:
        return picked
    return sentences[:limit]


def _build_thinking(content: str) -> str:
    if any(word in content for word in ["监管", "政策", "法规", "市场监督", "广告法"]):
        return "这类信息应优先进入合规观察清单，后续内容生产要把“能说什么、不能说什么”沉淀为表达边界。"
    if any(word in content for word in ["AI", "人工智能", "数字化", "数据", "数智"]):
        return "数字化和 AI 相关信号值得关注，但落地时要回到业务场景，优先判断能否提升选题、获客、合规审核和私域转化效率。"
    if any(word in content for word in ["营养", "保健食品", "功能食品", "膳食"]):
        return "营养健康内容有传播价值，但容易滑向功效承诺，适合用科普、场景和生活方式建议来表达。"
    if any(word in content for word in ["直销", "新零售", "私域", "社交零售"]):
        return "这类信息对渠道和私域运营有参考价值，重点不是复制话术，而是观察组织能力、用户信任和合规边界的变化。"
    return "这条信息可作为选题素材，但发布前还需要结合机构定位、目标人群和合规边界做二次判断。"


def _clean_noise(content: str) -> str:
    noise_words = [
        "首页",
        "新闻",
        "人物",
        "特别策划",
        "联系我们",
        "关于我们",
        "版权声明",
        "免责声明",
        "上一篇",
        "下一篇",
        "分享到",
    ]
    cleaned = content
    for word in noise_words:
        cleaned = cleaned.replace(word, " ")
    return " ".join(cleaned.split())
    seen = set()
    for sentence in sentences:
        normalized = sentence[:60]
        if normalized in seen:
            continue
        seen.add(normalized)
        if len(sentence) < 8:
            continue
        useful.append(sentence)
        if len(useful) == 3:
            break

    return "。".join(useful)[:220] + ("。" if useful else "")
