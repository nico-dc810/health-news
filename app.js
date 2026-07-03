const radarState = {
  activeCategory: "hot",
  query: "",
  signals: [],
  sourceHealth: { healthy: 20, total: 20 },
  updatedAt: "",
  activeDate: "",
  availableBriefs: [],
  calendarYear: null,
  calendarMonth: null,
  activeView: "hot",
};

const categories = [
  { id: "hot", label: "全部" },
  { id: "policy", label: "监管政策" },
  { id: "industry", label: "直销行业" },
  { id: "product", label: "产品监管" },
  { id: "research", label: "合规研究" },
  { id: "consumer", label: "健康素材" },
  { id: "media", label: "媒体线索" },
  { id: "community", label: "社媒观察" },
];

const categoryIcons = {
  policy: "📋",
  industry: "▣",
  product: "✚",
  research: "§",
  consumer: "●",
  media: "◈",
  community: "◎",
  hot: "◆",
};

const categoryColors = {
  policy: "tone-policy",
  industry: "tone-industry",
  product: "tone-product",
  research: "tone-research",
  consumer: "tone-consumer",
  media: "tone-media",
  community: "tone-community",
  hot: "tone-hot",
};

const fallbackSignals = [
  {
    rank: 1,
    category: "policy",
    source: "国家药监局",
    sourceCount: 1,
    priority: "A",
    time: "06/30 14:04",
    title: "国家药监局发布两项脑机接口医疗器械指导原则",
    summary: "脑机接口医疗器械产品分类界定和通用名称命名两项指导原则发布，新兴健康科技开始进入更清晰的分类和命名监管框架。",
    why: "脑机接口是健康科技前沿赛道，指导原则能帮助企业判断产品边界和注册路径。",
    tags: ["国家药监局", "医疗器械", "脑机接口"],
    url: "https://www.nmpa.gov.cn/directory/web/nmpa/xxgk/ggtg/ylqxggtg/ylqxqtggtg/20260630140449128.html",
  },
];

const interfaces = [
  ["行业资讯数据源", "GET /api/health/signals", "从行业来源读取政策、产业、产品、渠道和内容趋势。"],
  ["日报生成", "POST /api/radar/daily-report", "把今日重点信号整理成管理层日报、运营日报和选题清单。"],
  ["Agent 处理", "POST /api/agents/run", "保留给合规审核、选题生成、摘要改写、来源引用等能力。"],
  ["登录权限", "POST /api/auth/phone-login", "沿用手机号登录，后续可接企业账号、付款状态和权限组。"],
];

const $ = (selector) => document.querySelector(selector);

document.addEventListener("DOMContentLoaded", async () => {
  bindLogin();
  bindSearch();
  bindArchiveNavigator();
  bindDrawer();
  bindDetailView();
  renderCategories();
  await loadSignals();
  restoreSession();
});

function bindLogin() {
  $("#loginForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const phone = $("#loginPhone").value.trim();
    if (!/^1\d{10}$/.test(phone)) {
      setLoginMessage("请输入正确的 11 位手机号。", true);
      return;
    }

    const result = await tryApi("/api/auth/phone-login", {
      method: "POST",
      body: JSON.stringify({ phone }),
    });

    if (result && result.ok === false) {
      setLoginMessage(result.message || "该手机号暂未开通。", true);
      return;
    }

    window.localStorage.setItem("health-radar-user", JSON.stringify({ phone, loginAt: Date.now() }));
    enterApp();
  });
}

function restoreSession() {
  const saved = window.localStorage.getItem("health-radar-user");
  if (saved) enterApp();
}

function enterApp() {
  $("#loginView").classList.add("is-hidden");
  $("#appShell").classList.remove("is-hidden");
  renderSignals();
}

function setLoginMessage(message, isError) {
  const el = $("#loginMessage");
  el.textContent = message;
  el.classList.toggle("error", Boolean(isError));
}

function bindSearch() {
  $("#searchInput").addEventListener("input", (event) => {
    radarState.query = event.target.value.trim().toLowerCase();
    const archiveSearch = $("#archiveSearchInput");
    if (archiveSearch && archiveSearch.value !== event.target.value) archiveSearch.value = event.target.value;
    renderSignals();
  });

  document.querySelectorAll(".view-toggle button").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".view-toggle button").forEach((item) => item.classList.remove("is-active"));
      button.classList.add("is-active");
      radarState.activeView = button.dataset.view;
      renderSignals();
    });
  });
}

function bindArchiveNavigator() {
  const archiveSearch = $("#archiveSearchInput");
  if (archiveSearch) {
    archiveSearch.addEventListener("input", (event) => {
      radarState.query = event.target.value.trim().toLowerCase();
      const mainSearch = $("#searchInput");
      if (mainSearch && mainSearch.value !== event.target.value) mainSearch.value = event.target.value;
      renderSignals();
    });
  }

  $("#calendarPrev")?.addEventListener("click", () => shiftCalendarMonth(-1));
  $("#calendarNext")?.addEventListener("click", () => shiftCalendarMonth(1));
  $("#calendarGrid")?.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-calendar-date]");
    if (!button || button.disabled) return;
    await switchBriefDate(button.dataset.calendarDate);
  });
  $("#monthBriefList")?.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-brief-date]");
    if (!button) return;
    await switchBriefDate(button.dataset.briefDate);
  });
  $("#viewAllArchive")?.addEventListener("click", (event) => {
    event.preventDefault();
    document.querySelector(".archive-navigator").scrollIntoView({ behavior: "smooth" });
  });
}

function bindDrawer() {
  $("#agentButton").addEventListener("click", openDrawer);
  $("#drawerBackdrop").addEventListener("click", closeDrawer);
  $("#drawerClose").addEventListener("click", closeDrawer);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeDrawer();
  });
}

function openDrawer() {
  $("#agentDrawer").classList.add("is-open");
  $("#agentDrawer").setAttribute("aria-hidden", "false");
}

function closeDrawer() {
  $("#agentDrawer").classList.remove("is-open");
  $("#agentDrawer").setAttribute("aria-hidden", "true");
}

function bindDetailView() {
  $("#signalGrid").addEventListener("click", (event) => {
    const titleButton = event.target.closest("[data-open-detail]");
    if (!titleButton) return;
    const item = radarState.signals.find((signal) => signal.id === titleButton.dataset.openDetail);
    if (item) openDetail(item);
  });

  $("#detailClose").addEventListener("click", closeDetail);
  $("#detailBreadcrumb").addEventListener("click", (event) => {
    const target = event.target.closest("[data-detail-nav]");
    if (!target) return;
    if (target.dataset.detailNav === "brief") {
      closeDetail();
      return;
    }
    if (target.dataset.detailNav === "category") {
      radarState.activeCategory = target.dataset.category || "hot";
      renderCategories();
      renderSignals();
      closeDetail();
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeDetail();
  });
}

function openDetail(item) {
  $("#detailBreadcrumb").innerHTML = `
    <button type="button" data-detail-nav="brief">每日简报</button>
    <span>›</span>
    <button type="button" data-detail-nav="category" data-category="${escapeHtml(item.category)}">${escapeHtml(categoryLabel(item.category))}</button>
    <span>›</span>
    <time>${escapeHtml(formatDate(item.publishedAt || item.updatedAt))}</time>
  `;
  $("#detailTitle").textContent = item.title;

  const priorityClass = `priority-${String(item.priority || "c").toLowerCase()}`;
  $("#detailMeta").innerHTML = `
    <span class="${priorityClass}">优先级 ${escapeHtml(item.priority)}</span>
    <span>${escapeHtml(item.source)}</span>
    <span>${escapeHtml(formatDate(item.publishedAt || item.updatedAt))}</span>
    <span>${escapeHtml((item.tags || []).join(" / "))}</span>
  `;

  $("#detailSummary").innerHTML = renderStructuredSummary(item);
  $("#detailWhy").textContent = item.why;
  $("#detailMediaPotential").textContent = item.mediaPotential || inferMediaPotential(item);
  $("#detailCompliance").textContent = item.complianceNote || inferComplianceNote(item);
  $("#detailEvidence").innerHTML = renderEvidence(item);

  const sourceLink = $("#detailSource");
  sourceLink.href = item.url || "#";
  sourceLink.classList.toggle("is-hidden", !item.url);

  $("#detailDrawer").classList.remove("is-hidden");
  $("#detailDrawer").setAttribute("aria-hidden", "false");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function closeDetail() {
  $("#detailDrawer").classList.add("is-hidden");
  $("#detailDrawer").setAttribute("aria-hidden", "true");
}

function renderCategories() {
  const tabs = $("#categoryTabs");
  if (!tabs) return;

  const visibleCategories = categories.filter((category) => {
    if (category.id === "hot") return true;
    return categoryCount(category.id) > 0;
  });

  tabs.innerHTML = visibleCategories
    .map(
      (item) => `
        <button type="button" class="${item.id === radarState.activeCategory ? "is-active" : ""}" data-category="${item.id}">
          ${categoryIcon(item.id)} ${item.label} <b>${categoryCount(item.id)}</b>
        </button>
      `,
    )
    .join("");

  tabs.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      radarState.activeCategory = button.dataset.category;
      renderCategories();
      renderSignals();
    });
  });
}

async function loadSignals(date) {
  if (!radarState.availableBriefs.length) {
    await loadBriefIndex();
  }
  const selectedDate = date || radarState.activeDate || radarState.availableBriefs[0]?.date || "";
  const dailyPath = selectedDate ? `data/daily/${selectedDate}.json` : "";
  const data = (dailyPath ? await tryApi(dailyPath) : null) || (await tryApi("data/latest.json")) || (await tryApi("api/health/signals?limit=20"));
  radarState.activeDate = data?.date || selectedDate || formatDateForFile(data?.updated_at || new Date().toISOString());
  radarState.updatedAt = data?.updated_at || new Date().toISOString();
  if (data?.source_health) {
    radarState.sourceHealth = {
      healthy: data.source_health.healthy || radarState.sourceHealth.healthy,
      total: data.source_health.total || radarState.sourceHealth.total,
    };
  }
  radarState.signals = normalizeSignals(data) || fallbackSignals;
  setCalendarMonthFromDate(radarState.activeDate);
  updateStats(data?.updated_at);
  renderCategories();
  renderArchiveNavigator();
  renderRecentBriefs();
}

async function loadBriefIndex() {
  const index = await tryApi("data/daily/index.json");
  const list = Array.isArray(index?.items) ? index.items : [];
  radarState.availableBriefs = list.length
    ? list
    : [{ date: formatDateForFile(new Date().toISOString()), label: formatDate(new Date().toISOString()), path: "data/latest.json" }];
  setCalendarMonthFromDate(radarState.availableBriefs[0]?.date);
}

function normalizeSignals(data) {
  const list = Array.isArray(data) ? data : data?.items || data?.signals;
  if (!Array.isArray(list) || !list.length) return null;
  return list.map((item, index) => ({
    id: item.id || `signal-${index + 1}`,
    rank: item.rank || index + 1,
    category: item.category || "hot",
    source: item.source || item.source_name || "行业资讯",
    sourceCount: item.source_count || 1,
    priority: normalizePriority(item.priority || item.priority_level),
    time: item.time || formatTime(item.published_at || item.updated_at),
    publishedAt: item.published_at || item.updated_at || data?.updated_at,
    updatedAt: item.updated_at || data?.updated_at,
    title: item.title || "未命名信号",
    summary: item.summary || item.excerpt || item.raw_text || "暂无摘要。",
    detail: item.detail || item.full_summary || item.summary || "暂无概要介绍。",
    keyPoints: item.key_points || item.keyPoints || [],
    mediaPotential: item.media_potential || item.mediaPotential || "",
    complianceNote: item.compliance_note || item.complianceNote || "",
    consumerAngle: item.consumer_angle || item.consumerAngle || "",
    rewriteFormats: item.rewrite_formats || item.rewriteFormats || [],
    safeClaims: item.safe_claims || item.safeClaims || [],
    avoidClaims: item.avoid_claims || item.avoidClaims || [],
    evidenceLevel: item.evidence_level || item.evidenceLevel || "",
    action: item.action || "",
    imageUrl: normalizeUrl(item.image_url || item.imageUrl || item.cover || item.cover_url),
    why: item.why || item.reason || "已进入行业情报库，可继续交给 Agent 做摘要、选题或合规复核。",
    tags: item.tags || [],
    url: normalizeUrl(item.url || item.source_url),
  }));
}

function normalizePriority(value) {
  if (!value) return "C";
  const normalized = String(value).toUpperCase();
  if (normalized === "P0" || normalized === "A" || normalized === "10" || normalized === "9" || normalized === "8") return "A";
  if (normalized === "P1" || normalized === "B" || normalized === "7" || normalized === "6" || normalized === "5") return "B";
  return "C";
}

function renderStructuredSummary(item) {
  const points = buildReaderDigest(item);
  return points
    .map(
      (point, index) => `
        <article class="summary-point">
          <strong><span>${String(index + 1).padStart(2, "0")}</span>${escapeHtml(point.label)}</strong>
          <p>${escapeHtml(point.text)}</p>
        </article>
      `,
    )
    .join("");
}

function buildReaderDigest(item) {
  const keyPoints = Array.isArray(item.keyPoints) ? item.keyPoints : [];
  const usefulPoints = keyPoints.filter((point) => point?.text && !isGenericSummaryText(point.text));
  const sourceLine = item.source ? `${item.source} 这篇内容` : "这篇内容";
  const detailText = cleanText(item.detail || item.summary);
  const summaryText = cleanText(item.summary);
  const whyText = cleanText(item.why);
  const mediaText = cleanText(item.mediaPotential || inferMediaPotential(item));
  const complianceText = cleanText(item.complianceNote || inferComplianceNote(item));
  const tagText = (item.tags || []).slice(0, 4).join("、");

  const what = [
    `${sourceLine}主要讲的是：${summaryText || item.title}。`,
    detailText && detailText !== summaryText ? detailText : "",
    usefulPoints[0]?.text && usefulPoints[0].text !== summaryText ? usefulPoints[0].text : "",
  ]
    .filter(Boolean)
    .join("");

  const logic = [
    whyText ? `它重要的原因在于：${whyText}` : "",
    usefulPoints[1]?.text && usefulPoints[1].text !== whyText ? usefulPoints[1].text : "",
    tagText ? `从标签看，核心关联点是 ${tagText}。` : "",
  ]
    .filter(Boolean)
    .join("");

  const judgment = [
    mediaText ? `如果你是内容创作者或从业者，可以把它转化为：${mediaText}` : "",
    complianceText ? `阅读和转述时要注意：${complianceText}` : "",
    usefulPoints[2]?.text && usefulPoints[2].text !== mediaText ? usefulPoints[2].text : "",
    item.url ? "如果你需要核对原始事实、引用具体数据或判断适用范围，建议继续点开原文。" : "",
  ]
    .filter(Boolean)
    .join("");

  return [
    { label: "文章在讲什么", text: trimDigest(what || summaryText || item.title) },
    { label: "逻辑、因果和结论", text: trimDigest(logic || whyText || detailText) },
    { label: "读者如何判断价值", text: trimDigest(judgment || mediaText || complianceText) },
  ].filter((point) => point.text);
}

function isGenericSummaryText(text) {
  return /事实基础清楚|判断价值不在于标题热度|从业者可把它改写成案例拆解|避免功效夸大/.test(String(text || ""));
}

function cleanText(text) {
  return String(text || "").replace(/\s+/g, " ").trim();
}

function trimDigest(text) {
  const clean = cleanText(text);
  if (clean.length <= 420) return clean;
  const sentences = splitChineseSentences(clean);
  const selected = [];
  let length = 0;
  for (const sentence of sentences) {
    if (length + sentence.length > 420 && selected.length >= 2) break;
    selected.push(sentence);
    length += sentence.length;
  }
  const result = selected.join("");
  return result || `${clean.slice(0, 418)}…`;
}

function splitChineseSentences(text) {
  return String(text || "")
    .replace(/\s+/g, "")
    .match(/[^。！？；]+[。！？；]?/g) || [];
}

function renderEvidence(item) {
  const parts = [];

  if (item.evidenceLevel) {
    parts.push(`
      <div class="evidence-row">
        <span class="evidence-label">证据等级</span>
        <span class="evidence-value">${escapeHtml(item.evidenceLevel)}</span>
      </div>
    `);
  }

  if (item.source) {
    parts.push(`
      <div class="evidence-row">
        <span class="evidence-label">信息来源</span>
        <span class="evidence-value">${escapeHtml(item.source)}</span>
      </div>
    `);
  }

  if (item.url) {
    parts.push(`
      <div class="evidence-row">
        <span class="evidence-label">原文链接</span>
        <a class="evidence-value" href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">${escapeHtml(item.url)}</a>
      </div>
    `);
  }

  if (item.safeClaims?.length) {
    parts.push(`
      <div class="evidence-row">
        <span class="evidence-label">可用表述</span>
        <div class="safe-claims">
          ${item.safeClaims.map((claim) => `<span>${escapeHtml(claim)}</span>`).join("")}
        </div>
      </div>
    `);
  }

  if (item.avoidClaims?.length) {
    parts.push(`
      <div class="evidence-row">
        <span class="evidence-label">避免表述</span>
        <div class="avoid-claims">
          ${item.avoidClaims.map((claim) => `<span>${escapeHtml(claim)}</span>`).join("")}
        </div>
      </div>
    `);
  }

  if (item.rewriteFormats?.length) {
    parts.push(`
      <div class="evidence-row">
        <span class="evidence-label">推荐改写</span>
        <div class="signal-tags">
          ${item.rewriteFormats.map((format) => `<span>${escapeHtml(format)}</span>`).join("")}
        </div>
      </div>
    `);
  }

  return parts.length ? parts.join("") : "<p class=\"evidence-value\">暂无额外证据信息。</p>";
}

function inferMediaPotential(item) {
  const tagText = (item.tags || []).join("、");
  if (item.category === "product") return `适合改写成“产品资质/销售合规/选购避坑”类内容，可结合 ${tagText || "监管信息"} 做清单式科普。`;
  if (item.category === "research") return `适合改写成合规提醒或案例复盘，重点讲清边界，不建议做夸张标题。`;
  if (item.category === "media") return `适合作为选题线索或海外观察，建议补充国内监管语境后再发布。`;
  if (item.category === "policy") return `适合解读监管框架和影响边界，帮助从业者理解合规要求。`;
  return `适合改写成行业观察或竞品案例，面向从业者解释趋势和可借鉴点。`;
}

function inferComplianceNote(item) {
  const text = [item.title, item.summary, item.detail, item.why, ...(item.tags || [])].join(" ");
  if (/保健食品|医疗器械|药监|功效|广告|合规|MLM|金字塔|直销/.test(text)) {
    return "发布自媒体内容时应保留原始来源，避免扩大功效、暗示治疗效果、承诺收益或把个案经验包装成普遍结论。";
  }
  return "发布时应保留原文链接和时间，不把媒体观点直接写成事实结论。";
}

function updateStats(updatedAt) {
  const total = radarState.signals.length;
  const priorityA = radarState.signals.filter((item) => item.priority === "A").length;
  const selected = Math.min(20, radarState.signals.length || 20);

  $("#totalCount").textContent = String(total);
  $("#priorityCount").textContent = String(priorityA);
  $("#selectedCount").textContent = String(selected);
  $("#updatedAt").textContent = formatTime(updatedAt || new Date().toISOString());

  const displayDate = formatDateFromFile(radarState.activeDate) || formatDate(updatedAt || radarState.updatedAt);
  $("#briefDate").textContent = displayDate;
  $("#panelTitle").textContent = `每日简报 · ${displayDate}`;
  $("#panelSubtitle").textContent = `${total} 条信号 · ${priorityA} 条高优先级`;
}

function renderArchiveNavigator() {
  renderCalendar();
  renderMonthBriefList();
}

function renderCalendar() {
  const grid = $("#calendarGrid");
  if (!grid) return;
  const year = radarState.calendarYear || new Date().getFullYear();
  const month = Number.isInteger(radarState.calendarMonth) ? radarState.calendarMonth : new Date().getMonth();
  const available = new Set(radarState.availableBriefs.map((item) => item.date));
  const cells = [];
  for (let index = 0; index < firstDayOffsetMonday(year, month); index += 1) {
    cells.push('<span class="calendar-empty" aria-hidden="true"></span>');
  }
  for (let day = 1; day <= daysInMonth(year, month); day += 1) {
    const date = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    const hasBrief = available.has(date);
    const active = date === radarState.activeDate;
    cells.push(`
      <button
        type="button"
        class="calendar-day ${hasBrief ? "has-brief" : ""} ${active ? "is-active" : ""}"
        data-calendar-date="${escapeHtml(date)}"
        ${hasBrief ? "" : "disabled"}
        aria-label="${escapeHtml(formatChineseShortDate(date))}${hasBrief ? " brief" : ""}"
      >${day}</button>
    `);
  }
  $("#calendarMonthLabel").textContent = `${year} 年 ${month + 1} 月`;
  grid.innerHTML = cells.join("");
}

function renderMonthBriefList() {
  const list = $("#monthBriefList");
  if (!list) return;
  const year = radarState.calendarYear || new Date().getFullYear();
  const month = Number.isInteger(radarState.calendarMonth) ? radarState.calendarMonth : new Date().getMonth();
  const monthKey = `${year}-${String(month + 1).padStart(2, "0")}`;
  const items = radarState.availableBriefs
    .filter((item) => String(item.date || "").startsWith(monthKey))
    .sort((a, b) => String(b.date).localeCompare(String(a.date)));

  list.innerHTML = items.length
    ? items
        .map(
          (item) => `
            <button type="button" class="month-brief-item ${item.date === radarState.activeDate ? "is-active" : ""}" data-brief-date="${escapeHtml(item.date)}">
              <strong>${escapeHtml(item.title || item.label || "大健康简报")}</strong>
              <span>${escapeHtml(formatChineseShortDate(item.date))} · ${Number(item.count || item.total || 20)} 篇文章</span>
            </button>
          `,
        )
        .join("")
    : '<p class="month-empty">本月暂无已上线简报</p>';
}

function renderRecentBriefs() {
  const container = $("#recentBriefs");
  if (!container) return;

  const items = [...radarState.availableBriefs]
    .filter((item) => item.date !== radarState.activeDate)
    .sort((a, b) => String(b.date).localeCompare(String(a.date)))
    .slice(0, 3);

  container.innerHTML = items.length
    ? items
        .map(
          (item) => `
            <a href="#" class="recent-brief-card" data-brief-date="${escapeHtml(item.date)}">
              <strong>${escapeHtml(item.title || item.label || "大健康简报")}</strong>
              <span>${escapeHtml(formatChineseShortDate(item.date))} · ${Number(item.count || item.total || 20)} 篇文章</span>
            </a>
          `,
        )
        .join("")
    : '<p class="month-empty">暂无近期简报</p>';

  container.querySelectorAll(".recent-brief-card").forEach((card) => {
    card.addEventListener("click", async (event) => {
      event.preventDefault();
      await switchBriefDate(card.dataset.briefDate);
    });
  });
}

async function switchBriefDate(date) {
  if (!date || date === radarState.activeDate) return;
  radarState.activeDate = date;
  setCalendarMonthFromDate(date, true);
  await loadSignals(date);
  renderSignals();
}

function setCalendarMonthFromDate(dateString, force = false) {
  if (!dateString || (!force && radarState.calendarYear !== null)) return;
  const match = String(dateString).match(/^(\d{4})-(\d{2})-\d{2}$/);
  if (!match) return;
  radarState.calendarYear = Number(match[1]);
  radarState.calendarMonth = Number(match[2]) - 1;
}

function shiftCalendarMonth(delta) {
  const year = radarState.calendarYear || new Date().getFullYear();
  const month = Number.isInteger(radarState.calendarMonth) ? radarState.calendarMonth : new Date().getMonth();
  const date = new Date(year, month + delta, 1);
  radarState.calendarYear = date.getFullYear();
  radarState.calendarMonth = date.getMonth();
  renderArchiveNavigator();
}

function categoryCount(categoryId) {
  if (categoryId === "hot") return radarState.signals.length || fallbackSignals.length;
  return radarState.signals.filter((item) => item.category === categoryId).length;
}

function categoryLabel(categoryId) {
  return categories.find((category) => category.id === categoryId)?.label || "行业信号";
}

function categoryIcon(categoryId) {
  return categoryIcons[categoryId] || "◆";
}

function categoryToneClass(categoryId) {
  return categoryColors[categoryId] || "tone-hot";
}

function renderSignals() {
  const items = filteredSignals();
  $("#resultMeta").textContent = `行业信号 · ${items.length || 0} 条`;
  $("#signalGrid").innerHTML = items.length
    ? renderSignalGroups(items)
    : `<article class="signal-card"><h3>没有匹配的资讯</h3><p>换一个关键词，或切回热点分类。</p></article>`;
}

function filteredSignals() {
  const query = radarState.query;
  let items = radarState.signals.filter((item) => {
    const categoryMatch = radarState.activeCategory === "hot" || item.category === radarState.activeCategory;
    const haystack = [item.title, item.summary, item.source, item.why, ...(item.tags || [])].join(" ").toLowerCase();
    return categoryMatch && (!query || haystack.includes(query));
  });

  if (radarState.activeView === "hot") {
    items = items.filter((item) => item.priority === "A").slice(0, 10);
  }

  return items;
}

function renderSignalGroups(items) {
  if (radarState.activeCategory !== "hot") {
    return `
      <section class="brief-group ${categoryToneClass(radarState.activeCategory)}">
        <div class="brief-group-head">
          <span class="group-icon">${categoryIcon(radarState.activeCategory)}</span>
          <div>
            <h3>${escapeHtml(categoryLabel(radarState.activeCategory))}</h3>
            <span>每日简报 · ${escapeHtml(formatDate(radarState.updatedAt))} · ${items.length} 条</span>
          </div>
        </div>
        <div class="brief-list">${items.map(renderSignalCard).join("")}</div>
      </section>
    `;
  }

  const groups = categories
    .filter((category) => category.id !== "hot")
    .map((category) => ({
      ...category,
      items: items.filter((item) => item.category === category.id),
    }))
    .filter((group) => group.items.length);

  const ungrouped = items.filter((item) => !categories.some((category) => category.id === item.category));
  if (ungrouped.length) groups.push({ id: "other", label: "其他信号", items: ungrouped });

  return groups
    .map(
      (group) => `
        <section class="brief-group ${categoryToneClass(group.id)}">
          <div class="brief-group-head">
            <span class="group-icon">${categoryIcon(group.id)}</span>
            <div>
              <h3>${escapeHtml(group.label)}</h3>
              <span>每日简报 · ${escapeHtml(formatDate(radarState.updatedAt))} · ${group.items.length} 条</span>
            </div>
          </div>
          <div class="brief-list">${group.items.map(renderSignalCard).join("")}</div>
        </section>
      `,
    )
    .join("");
}

function renderSignalCard(item) {
  const priorityClass = `priority-${String(item.priority || "c").toLowerCase()}`;
  const sourceLink = item.url
    ? `<a href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">查看原文 →</a>`
    : `<span class="source-unavailable">暂无原文</span>`;

  return `
    <article class="signal-card ${categoryToneClass(item.category)}">
      <span class="signal-rank">${String(item.rank).padStart(2, "0")}</span>
      <div class="brief-copy">
        <button type="button" class="brief-title" data-open-detail="${escapeHtml(item.id)}">${escapeHtml(item.title)}</button>
        <p>${escapeHtml(item.summary)}</p>
        <div class="signal-meta">
          <em class="${priorityClass}">优先级 ${escapeHtml(item.priority)}</em>
          <span class="source-tag">${escapeHtml(item.source)}</span>
          <small>${escapeHtml(formatDate(item.publishedAt || item.updatedAt))}</small>
        </div>
        <div class="signal-tags">
          ${(item.tags || []).slice(0, 4).map((tag) => `<span>${escapeHtml(tag)}</span>`).join("")}
        </div>
      </div>
      <div class="brief-action">
        ${sourceLink}
      </div>
    </article>
  `;
}

async function tryApi(path, options = {}) {
  try {
    const response = await fetch(path, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
    if (!response.ok) return null;
    return await response.json();
  } catch (_) {
    return null;
  }
}

function formatTime(value) {
  const date = value ? new Date(value) : new Date();
  if (Number.isNaN(date.getTime())) return "--/-- --:--";
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hour = String(date.getHours()).padStart(2, "0");
  const minute = String(date.getMinutes()).padStart(2, "0");
  return `${month}/${day} ${hour}:${minute}`;
}

function formatDate(value) {
  const date = value ? new Date(value) : new Date();
  if (Number.isNaN(date.getTime())) return "----/--/--";
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}/${month}/${day}`;
}

function formatDateForFile(value) {
  const date = value ? new Date(value) : new Date();
  if (Number.isNaN(date.getTime())) return "";
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatDateFromFile(value) {
  if (!value) return "";
  const match = String(value).match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return "";
  return `${match[1]}/${match[2]}/${match[3]}`;
}

function formatChineseShortDate(value) {
  const match = String(value || "").match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return "";
  return `${Number(match[2])} 月 ${Number(match[3])} 日`;
}

function daysInMonth(year, month) {
  return new Date(year, month + 1, 0).getDate();
}

function firstDayOffsetMonday(year, month) {
  return (new Date(year, month, 1).getDay() + 6) % 7;
}

function normalizeUrl(value) {
  if (!value || value === "#") return "";
  const url = String(value).trim();
  if (/^https?:\/\//i.test(url)) return url;
  if (/^[\w.-]+\.[a-z]{2,}(\/.*)?$/i.test(url)) return `https://${url}`;
  return "";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
