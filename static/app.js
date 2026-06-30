const radarState = {
  activeCategory: "hot",
  query: "",
  signals: [],
  sourceHealth: { healthy: 20, total: 20 },
};

const categories = [
  { id: "hot", label: "热点", count: 679 },
  { id: "model", label: "模型", count: 155 },
  { id: "product", label: "产品", count: 164 },
  { id: "developer", label: "开发者", count: 183 },
  { id: "health", label: "HN热议", count: 92 },
  { id: "industry", label: "行业", count: 245 },
  { id: "research", label: "研究", count: 28 },
  { id: "media", label: "自媒体", count: 31 },
  { id: "community", label: "社区", count: 258 },
];

const fallbackSignals = [
  {
    rank: 1,
    category: "hot",
    source: "TopHub",
    sourceCount: 1,
    priority: "C",
    time: "06/30 08:03",
    title: "AI 能源使用的环境成本：碳足迹、水足迹与土地足迹",
    summary: "围绕 AI 算力增长带来的能源、水资源与土地使用展开讨论，适合追踪 AI 基础设施与可持续发展之间的长期矛盾。",
    why: "健康科技和 AI 医疗产品后续会持续面对算力成本、绿色合规和 ESG 叙事压力。",
    tags: ["AI基础设施", "ESG", "产业趋势"],
    url: "https://example.com/ai-energy-cost",
  },
  {
    rank: 2,
    category: "developer",
    source: "TopHub",
    sourceCount: 1,
    priority: "C",
    time: "06/30 08:03",
    title: "中国开源大模型如何真正实现「价值出海」？",
    summary: "值得关注方向的新近更新，讨论国产模型在国际市场中的开发者生态、工具链、部署成本和场景落地。",
    why: "大健康内容和智能体产品可优先评估国产模型的私有化部署、成本和合规边界。",
    tags: ["开源模型", "出海", "开发者生态"],
    url: "https://example.com/china-open-models",
  },
  {
    rank: 3,
    category: "product",
    source: "行业资讯",
    sourceCount: 4,
    priority: "B",
    time: "06/30 07:42",
    title: "AI 健康管理产品开始从问答工具转向连续陪伴式服务",
    summary: "多家健康科技团队把体重管理、睡眠、营养记录和慢病教育整合进长期服务流程。",
    why: "内容平台可以从单篇资讯扩展到专题、用户问题库和服务路径拆解。",
    tags: ["健康管理", "AI产品", "服务设计"],
    url: "https://example.com/ai-health-product",
  },
  {
    rank: 4,
    category: "industry",
    source: "企业知识库",
    sourceCount: 6,
    priority: "A",
    time: "06/30 07:10",
    title: "监管趋严背景下，营养健康内容需要更强的来源引用",
    summary: "围绕功效表达、用户案例、达人种草和直播话术的边界，行业内正在形成更高的审核要求。",
    why: "这是大健康智媒体平台的核心场景，后续应把来源引用和合规提示做成默认能力。",
    tags: ["合规", "内容审核", "知识库"],
    url: "https://example.com/health-compliance",
  },
  {
    rank: 5,
    category: "research",
    source: "论文追踪",
    sourceCount: 2,
    priority: "B",
    time: "06/30 06:58",
    title: "多模态模型在医学影像辅助阅读中的可解释性仍是落地瓶颈",
    summary: "研究讨论模型输出稳定性、医生信任和审计记录的重要性，强调临床场景不能只看准确率。",
    why: "适合做医学 AI 专题，也能作为产品设计中的风险控制依据。",
    tags: ["医学AI", "多模态", "可解释性"],
    url: "https://example.com/medical-ai-explainability",
  },
  {
    rank: 6,
    category: "media",
    source: "自媒体",
    sourceCount: 3,
    priority: "C",
    time: "06/30 06:35",
    title: "小红书健康内容从知识科普转向「轻量计划」包装",
    summary: "热门内容更强调 7 天计划、清单、打卡和低门槛行动，而不是长篇专家式解释。",
    why: "可直接转化为内容选题、私域运营和健康产品陪伴式服务模板。",
    tags: ["小红书", "内容运营", "私域"],
    url: "https://example.com/xhs-health-content",
  },
];

const interfaces = [
  ["IMA 知识库数据源", "GET /api/ima/signals", "从 IMA 知识库读取资讯、笔记、网页收藏和标签。"],
  ["日报生成", "POST /api/radar/daily-report", "把今日重点信号整理成管理层日报、运营日报和选题清单。"],
  ["Agent 接入", "POST /api/agents/run", "保留给合规审核、选题生成、摘要改写、来源引用等能力。"],
  ["登录权限", "POST /api/auth/phone-login", "沿用手机号登录，后续可接企业账号、付款状态和权限组。"],
];

const $ = (selector) => document.querySelector(selector);

document.addEventListener("DOMContentLoaded", async () => {
  bindLogin();
  bindSearch();
  bindDrawer();
  renderCategories();
  renderInterfaces();
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
    renderSignals();
  });

  document.querySelectorAll(".view-toggle button").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".view-toggle button").forEach((item) => item.classList.remove("is-active"));
      button.classList.add("is-active");
      renderSignals();
    });
  });
}

function bindDrawer() {
  $("#agentButton").addEventListener("click", openDrawer);
  $("#filterButton").addEventListener("click", openDrawer);
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

function renderCategories() {
  $("#categoryTabs").innerHTML = categories
    .map(
      (item) => `
        <button type="button" class="${item.id === radarState.activeCategory ? "is-active" : ""}" data-category="${item.id}">
          ${item.label} <b>${item.count}</b>
        </button>
      `,
    )
    .join("");

  $("#categoryTabs").querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      radarState.activeCategory = button.dataset.category;
      renderCategories();
      renderSignals();
    });
  });
}

async function loadSignals() {
  const data = await tryApi("/api/ima/signals?limit=20");
  radarState.signals = normalizeSignals(data) || fallbackSignals;
  updateStats();
}

function normalizeSignals(data) {
  const list = Array.isArray(data) ? data : data?.items || data?.signals;
  if (!Array.isArray(list) || !list.length) return null;
  return list.map((item, index) => ({
    rank: item.rank || index + 1,
    category: item.category || "hot",
    source: item.source || item.source_name || "IMA",
    sourceCount: item.source_count || 1,
    priority: item.priority || item.priority_level || "C",
    time: item.time || formatTime(item.published_at || item.updated_at),
    title: item.title || "未命名信号",
    summary: item.summary || item.excerpt || item.raw_text || "暂无摘要。",
    why: item.why || item.reason || "已进入知识库，可继续交给 Agent 处理。",
    tags: item.tags || [],
    url: item.url || item.source_url || "#",
  }));
}

function updateStats() {
  const total = categories.find((item) => item.id === "hot")?.count || radarState.signals.length;
  const selected = Math.min(20, radarState.signals.length || 20);
  $("#totalCount").textContent = String(total);
  $("#priorityCount").textContent = "84";
  $("#selectedCount").textContent = String(selected);
  $("#healthySourceCount").textContent = `${radarState.sourceHealth.healthy}/${radarState.sourceHealth.total}正常`;
  $("#sourceStatus").textContent = `${radarState.sourceHealth.healthy}/${radarState.sourceHealth.total} 源正常`;
  $("#updatedAt").textContent = formatTime(new Date().toISOString());
}

function renderSignals() {
  const items = filteredSignals();
  $("#resultMeta").textContent = `AI强相关 · ${items.length || 0} 条`;
  $("#filterMeta").textContent = `${items.length || 0} 条结果 · ${radarState.sourceHealth.healthy}/${radarState.sourceHealth.total} 源正常`;
  $("#signalGrid").innerHTML = items.length
    ? items.map(renderSignalCard).join("")
    : `<article class="signal-card"><h3>没有匹配的资讯</h3><p>换一个关键词，或切回热点分类。</p></article>`;
}

function filteredSignals() {
  const query = radarState.query;
  return radarState.signals.filter((item) => {
    const categoryMatch = radarState.activeCategory === "hot" || item.category === radarState.activeCategory;
    const haystack = [item.title, item.summary, item.source, item.why, ...(item.tags || [])].join(" ").toLowerCase();
    return categoryMatch && (!query || haystack.includes(query));
  });
}

function renderSignalCard(item) {
  const priorityClass = `priority-${String(item.priority || "c").toLowerCase()}`;
  return `
    <article class="signal-card">
      <div class="signal-meta">
        <span>#${escapeHtml(item.rank)}</span>
        <small>${escapeHtml(item.source)}</small>
        <small>${escapeHtml(item.sourceCount)} 个来源</small>
        <em class="${priorityClass}">优先级 ${escapeHtml(item.priority)}</em>
        <small>${escapeHtml(item.time)}</small>
      </div>
      <h3>${escapeHtml(item.title)}</h3>
      <p>${escapeHtml(item.summary)}</p>
      <div class="why-box">
        <strong>为什么重要</strong>
        <p>${escapeHtml(item.why)}</p>
      </div>
      <div class="signal-tags">${(item.tags || []).map((tag) => `<span>${escapeHtml(tag)}</span>`).join("")}</div>
      <a href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">查看原文</a>
    </article>
  `;
}

function renderInterfaces() {
  $("#interfaceGrid").innerHTML = interfaces
    .map(
      ([title, endpoint, desc]) => `
        <article class="interface-card">
          <strong>${title}</strong>
          <span>${endpoint}</span>
          <small>${desc}</small>
        </article>
      `,
    )
    .join("");
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
  if (Number.isNaN(date.getTime())) return "06/30 08:03";
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hour = String(date.getHours()).padStart(2, "0");
  const minute = String(date.getMinutes()).padStart(2, "0");
  return `${month}/${day} ${hour}:${minute}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
