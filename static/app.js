// ═══════════════════════════════════════
// 大健康 AI 资讯雷达 — 前端核心逻辑
// 版本: 20260702-auth1
// ═══════════════════════════════════════

// ── API 基地址 ──
const API_BASE = resolveApiBase();

function resolveApiBase() {
  const params = new URLSearchParams(window.location.search);
  if (params.get("api")) return params.get("api");
  // 本地调试走 localhost，生产走 Render
  if (/localhost|127\.0\.0\.1/.test(window.location.hostname)) {
    return "http://localhost:8000";
  }
  return "https://health-media-demo.onrender.com";
}

// ── 状态 ──
const authState = {
  token: null,
  phone: null,
  user: null,
};

const radarState = {
  activeCategory: "hot",
  query: "",
  signals: [],
  sourceHealth: { healthy: 20, total: 20 },
  updatedAt: "",
};

const categories = [
  { id: "hot", label: "全部" },
  { id: "industry", label: "直销行业" },
  { id: "product", label: "产品监管" },
  { id: "research", label: "合规研究" },
  { id: "media", label: "媒体线索" },
  { id: "community", label: "社媒观察" },
];

const fallbackSignals = [
  {
    rank: 1, category: "hot", source: "TopHub", sourceCount: 1, priority: "C",
    time: "06/30 08:03", title: "AI 能源使用的环境成本：碳足迹、水足迹与土地足迹",
    summary: "围绕 AI 算力增长带来的能源、水资源与土地使用展开讨论。",
    why: "健康科技和 AI 医疗产品后续会持续面对算力成本、绿色合规和 ESG 叙事压力。",
    tags: ["AI基础设施", "ESG", "产业趋势"], url: "https://example.com/ai-energy-cost",
  },
  {
    rank: 2, category: "developer", source: "TopHub", sourceCount: 1, priority: "C",
    time: "06/30 08:03", title: "中国开源大模型如何真正实现「价值出海」？",
    summary: "讨论国产模型在国际市场中的开发者生态、工具链、部署成本和场景落地。",
    why: "大健康内容和智能体产品可优先评估国产模型的私有化部署、成本和合规边界。",
    tags: ["开源模型", "出海", "开发者生态"], url: "https://example.com/china-open-models",
  },
  {
    rank: 3, category: "product", source: "行业资讯", sourceCount: 4, priority: "B",
    time: "06/30 07:42", title: "AI 健康管理产品开始从问答工具转向连续陪伴式服务",
    summary: "多家健康科技团队把体重管理、睡眠、营养记录和慢病教育整合进长期服务流程。",
    why: "内容平台可以从单篇资讯扩展到专题、用户问题库和服务路径拆解。",
    tags: ["健康管理", "AI产品", "服务设计"], url: "https://example.com/ai-health-product",
  },
  {
    rank: 4, category: "industry", source: "企业知识库", sourceCount: 6, priority: "A",
    time: "06/30 07:10", title: "监管趋严背景下，营养健康内容需要更强的来源引用",
    summary: "围绕功效表达、用户案例、达人种草和直播话术的边界。",
    why: "这是大健康智媒体平台的核心场景，后续应把来源引用和合规提示做成默认能力。",
    tags: ["合规", "内容审核", "知识库"], url: "https://example.com/health-compliance",
  },
  {
    rank: 5, category: "research", source: "论文追踪", sourceCount: 2, priority: "B",
    time: "06/30 06:58", title: "多模态模型在医学影像辅助阅读中的可解释性仍是落地瓶颈",
    summary: "研究讨论模型输出稳定性、医生信任和审计记录的重要性。",
    why: "适合做医学 AI 专题，也能作为产品设计中的风险控制依据。",
    tags: ["医学AI", "多模态", "可解释性"], url: "https://example.com/medical-ai-explainability",
  },
  {
    rank: 6, category: "media", source: "自媒体", sourceCount: 3, priority: "C",
    time: "06/30 06:35", title: "小红书健康内容从知识科普转向「轻量计划」包装",
    summary: "热门内容更强调 7 天计划、清单、打卡和低门槛行动。",
    why: "可直接转化为内容选题、私域运营和健康产品陪伴式服务模板。",
    tags: ["小红书", "内容运营", "私域"], url: "https://example.com/xhs-health-content",
  },
];

const interfaces = [
  ["行业资讯数据源", "GET /api/health/signals", "从行业来源读取政策、产业、产品、渠道和内容趋势。"],
  ["日报生成", "POST /api/radar/daily-report", "把今日重点信号整理成管理层日报、运营日报和选题清单。"],
  ["Agent 接入", "POST /api/agents/run", "保留给合规审核、选题生成、摘要改写、来源引用等能力。"],
  ["登录权限", "POST /api/auth/check-phone", "手机号验证 + 支付开通 + Token 自动续期。"],
];

const $ = (selector) => document.querySelector(selector);

// ═══════════════════════════════════════
// 启动
// ═══════════════════════════════════════

document.addEventListener("DOMContentLoaded", async () => {
  bindSearch();
  bindDrawer();
  bindDetailView();
  bindPaymentTabs();
  bindLogin();
  renderInterfaces();
  await loadSignals();
  await restoreSession();
});

// ═══════════════════════════════════════
// 认证：Token 恢复 → 验证 → 进入或重登
// ═══════════════════════════════════════

async function restoreSession() {
  const saved = readStorage("health-radar-token");
  const phone = readStorage("health-radar-phone");
  if (!saved || !phone) {
    showLoginView();
    return;
  }

  // 有 token → 先让后端验证
  showLoginView();
  setLoginMessage("正在验证登录状态...", false);
  $("#loginSubmit").disabled = true;

  const result = await apiPost("/api/auth/verify-token", { token: saved });
  if (result && result.ok) {
    authState.token = result.token;
    authState.phone = phone;
    authState.user = result.user;
    persistAuth(result.token, phone);
    enterApp();
    return;
  }

  // token 失效 → 清除并显示登录
  clearAuth();
  setLoginMessage("登录已过期，请重新输入手机号。", true);
  $("#loginSubmit").disabled = false;
}

function showLoginView() {
  $("#loginView").classList.remove("is-hidden");
  $("#appShell").classList.add("is-hidden");
  showPhoneStep();
}

function showPhoneStep() {
  $("#phoneStep").classList.remove("is-hidden");
  $("#paymentStep").classList.add("is-hidden");
  $("#blockedStep").classList.add("is-hidden");
  $("#loginMessage").classList.add("is-hidden");
  hidePaymentMessage();
  $("#loginSubmit").disabled = false;
}

// ═══════════════════════════════════════
// 登录表单绑定
// ═══════════════════════════════════════

function bindLogin() {
  $("#loginSubmit").addEventListener("click", handleLoginSubmit);
  $("#loginPhone").addEventListener("keydown", (event) => {
    if (event.key === "Enter") handleLoginSubmit();
  });
  $("#paymentBack").addEventListener("click", showPhoneStep);
  $("#paymentCheckButton").addEventListener("click", handlePaymentRetry);
  $("#logoutButton").addEventListener("click", handleLogout);
}

async function handleLoginSubmit() {
  const phone = $("#loginPhone").value.trim();
  if (!/^1\d{10}$/.test(phone)) {
    setLoginMessage("请输入正确的 11 位手机号。", true);
    return;
  }

  setButtonLoading($("#loginSubmit"), true);
  setLoginMessage("正在验证...", false);

  const result = await apiPost("/api/auth/check-phone", { phone });

  setButtonLoading($("#loginSubmit"), false);

  if (!result) {
    setLoginMessage("网络连接失败，请检查后端服务是否已启动。", true);
    return;
  }

  if (result.allowed && result.token) {
    // ✅ 已付款 → 保存 token，进入应用
    authState.token = result.token;
    authState.phone = phone;
    authState.user = result.user;
    persistAuth(result.token, phone);
    enterApp();
    return;
  }

  if (result.reason === "blocked") {
    // ❌ 被禁用
    showBlockedStep(result.message);
    return;
  }

  // 💰 未付款 → 显示支付页
  showPaymentStep(phone);
}

// ═══════════════════════════════════════
// 支付页
// ═══════════════════════════════════════

function showPaymentStep(phone) {
  $("#phoneStep").classList.add("is-hidden");
  $("#blockedStep").classList.add("is-hidden");
  $("#paymentStep").classList.remove("is-hidden");
  $("#loginMessage").classList.add("is-hidden");
  hidePaymentMessage();
  $("#paymentPhoneHint").textContent = `当前手机号：${maskPhone(phone)}`;
  // 默认显示微信
  switchPaymentTab("wechat");
}

function showBlockedStep(message) {
  $("#phoneStep").classList.add("is-hidden");
  $("#paymentStep").classList.add("is-hidden");
  $("#blockedStep").classList.remove("is-hidden");
  $("#blockedMessage").textContent = message;
}

function bindPaymentTabs() {
  document.querySelectorAll(".payment-tabs button").forEach((button) => {
    button.addEventListener("click", () => {
      switchPaymentTab(button.dataset.pay);
    });
  });
}

function switchPaymentTab(provider) {
  document.querySelectorAll(".payment-tabs button").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.pay === provider);
  });
  $("#paymentQrWechat").classList.toggle("is-hidden", provider !== "wechat");
  $("#paymentQrAlipay").classList.toggle("is-hidden", provider !== "alipay");
}

async function handlePaymentRetry() {
  const phone = $("#loginPhone").value.trim();
  if (!phone) {
    showPhoneStep();
    return;
  }

  setButtonLoading($("#paymentCheckButton"), true);
  setPaymentMessage("正在检测开通状态...", false);

  const result = await apiPost("/api/auth/check-phone", { phone });

  setButtonLoading($("#paymentCheckButton"), false);

  if (result && result.allowed && result.token) {
    authState.token = result.token;
    authState.phone = phone;
    authState.user = result.user;
    persistAuth(result.token, phone);
    enterApp();
  } else if (result && result.reason === "blocked") {
    showBlockedStep(result.message);
  } else if (result) {
    setPaymentMessage(result.message || "尚未开通，请付款后重试。", true);
  } else {
    setPaymentMessage("检测失败，请检查网络后重试。", true);
  }
}

function setPaymentMessage(message, isError) {
  const el = $("#paymentMessage");
  el.textContent = message;
  el.classList.remove("is-hidden");
  el.classList.toggle("error", Boolean(isError));
}

function hidePaymentMessage() {
  $("#paymentMessage").classList.add("is-hidden");
}

// ═══════════════════════════════════════
// 进入 / 退出应用
// ═══════════════════════════════════════

function enterApp() {
  $("#loginView").classList.add("is-hidden");
  $("#appShell").classList.remove("is-hidden");
  renderSignals();
}

function handleLogout() {
  clearAuth();
  $("#appShell").classList.add("is-hidden");
  showLoginView();
  $("#loginPhone").value = "";
  setLoginMessage("已退出登录。", false);
}

// ═══════════════════════════════════════
// 持久化
// ═══════════════════════════════════════

function persistAuth(token, phone) {
  writeStorage("health-radar-token", token);
  writeStorage("health-radar-phone", phone);
}

function clearAuth() {
  authState.token = null;
  authState.phone = null;
  authState.user = null;
  window.localStorage.removeItem("health-radar-token");
  window.localStorage.removeItem("health-radar-phone");
}

function readStorage(key) {
  try { return window.localStorage.getItem(key); } catch (_) { return null; }
}

function writeStorage(key, value) {
  try { window.localStorage.setItem(key, value); } catch (_) { /* quota exceeded */ }
}

// ═══════════════════════════════════════
// UI 辅助
// ═══════════════════════════════════════

function setLoginMessage(message, isError) {
  const el = $("#loginMessage");
  el.textContent = message;
  el.classList.remove("is-hidden");
  el.classList.toggle("error", Boolean(isError));
}

function setButtonLoading(button, loading) {
  button.classList.toggle("is-loading", loading);
  button.disabled = loading;
}

function maskPhone(phone) {
  if (!phone || phone.length < 7) return phone;
  return phone.slice(0, 3) + "****" + phone.slice(-4);
}

// ═══════════════════════════════════════
// API 调用
// ═══════════════════════════════════════

async function apiPost(path, body) {
  try {
    const headers = { "Content-Type": "application/json" };
    if (authState.token) {
      headers["Authorization"] = `Bearer ${authState.token}`;
    }
    const response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });
    if (!response.ok) return null;
    return await response.json();
  } catch (_) {
    return null;
  }
}

async function tryApi(path, options = {}) {
  try {
    // 本地数据文件用相对路径，API 调用加前缀
    const url = path.startsWith("data/") ? path : `${API_BASE}${path}`;
    const response = await fetch(url, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
    if (!response.ok) return null;
    return await response.json();
  } catch (_) {
    return null;
  }
}

// ═══════════════════════════════════════
// 搜索 / 筛选 / 抽屉 / 详情（保持不变）
// ═══════════════════════════════════════

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
  $("#detailMeta").innerHTML = `
    <span>${escapeHtml(item.source)}</span>
    <span>优先级 ${escapeHtml(item.priority)}</span>
    <span>${escapeHtml(formatDate(item.publishedAt || item.updatedAt))}</span>
    <span>${escapeHtml((item.tags || []).join(" / "))}</span>
  `;
  $("#detailHero").className = `detail-hero tone-${escapeHtml(item.category)}`;
  if (item.imageUrl) {
    $("#detailHero").innerHTML = `<img src="${escapeHtml(item.imageUrl)}" alt="${escapeHtml(item.title)}" loading="lazy" />`;
    $("#detailHero").classList.remove("is-hidden");
  } else {
    $("#detailHero").innerHTML = "";
    $("#detailHero").classList.add("is-hidden");
  }
  $("#detailSummary").innerHTML = renderStructuredSummary(item);
  $("#detailWhy").textContent = item.why;
  $("#detailMediaPotential").textContent = item.mediaPotential || inferMediaPotential(item);
  $("#detailCompliance").textContent = item.complianceNote || inferComplianceNote(item);
  $("#detailSource").href = item.url;
  $("#detailSource").classList.toggle("is-hidden", !item.url);
  $("#detailDrawer").classList.remove("is-hidden");
  $("#detailDrawer").setAttribute("aria-hidden", "false");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function closeDetail() {
  $("#detailDrawer").classList.add("is-hidden");
  $("#detailDrawer").setAttribute("aria-hidden", "true");
}

// ═══════════════════════════════════════
// 分类 / 信号加载 / 渲染
// ═══════════════════════════════════════

function renderCategories() {
  $("#categoryTabs").innerHTML = categories
    .map(
      (item) => `
        <button type="button" class="${item.id === radarState.activeCategory ? "is-active" : ""}" data-category="${item.id}">
          ${item.label} <b>${categoryCount(item.id)}</b>
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
  const data = (await tryApi("data/latest.json")) || (await tryApi("api/health/signals?limit=20"));
  radarState.updatedAt = data?.updated_at || new Date().toISOString();
  if (data?.source_health) {
    radarState.sourceHealth = {
      healthy: data.source_health.healthy || radarState.sourceHealth.healthy,
      total: data.source_health.total || radarState.sourceHealth.total,
    };
  }
  radarState.signals = normalizeSignals(data) || fallbackSignals;
  updateStats(data?.updated_at);
  renderCategories();
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
    priority: item.priority || item.priority_level || "C",
    time: item.time || formatTime(item.published_at || item.updated_at),
    publishedAt: item.published_at || item.updated_at || data?.updated_at,
    updatedAt: item.updated_at || data?.updated_at,
    title: item.title || "未命名信号",
    summary: item.summary || item.excerpt || item.raw_text || "暂无摘要。",
    detail: item.detail || item.full_summary || item.summary || "暂无概要介绍。",
    keyPoints: item.key_points || item.keyPoints || [],
    mediaPotential: item.media_potential || item.mediaPotential || "",
    complianceNote: item.compliance_note || item.complianceNote || "",
    action: item.action || "",
    imageUrl: normalizeUrl(item.image_url || item.imageUrl || item.cover || item.cover_url),
    why: item.why || item.reason || "已进入行业情报库，可继续交给 Agent 做摘要、选题或合规复核。",
    tags: item.tags || [],
    url: normalizeUrl(item.url || item.source_url),
  }));
}

function renderStructuredSummary(item) {
  const points = Array.isArray(item.keyPoints) && item.keyPoints.length ? item.keyPoints : buildSummaryPoints(item);
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

function buildSummaryPoints(item) {
  const sentences = splitChineseSentences(item.detail || item.summary);
  const what = sentences.slice(0, 2).join("");
  const trend = sentences.slice(2, 4).join("");
  const impact = sentences.slice(4).join("");
  const points = [
    { label: "这是什么", text: what || item.summary },
    { label: "行业信号", text: trend || item.why },
    { label: "从业者启发", text: impact || item.why },
  ];
  if (item.action) points.push({ label: "建议动作", text: item.action });
  return points.filter((point) => point.text);
}

function splitChineseSentences(text) {
  return String(text || "")
    .replace(/\s+/g, "")
    .match(/[^。！？；]+[。！？；]?/g) || [];
}

function inferMediaPotential(item) {
  const tagText = (item.tags || []).join("、");
  if (item.category === "product") return `适合改写成"产品资质/销售合规/选购避坑"类内容，可结合 ${tagText || "监管信息"} 做清单式科普。`;
  if (item.category === "research") return `适合改写成合规提醒或案例复盘，重点讲清边界，不建议做夸张标题。`;
  if (item.category === "media") return `适合作为选题线索或海外观察，建议补充国内监管语境后再发布。`;
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
  const selected = Math.min(20, radarState.signals.length || 20);
  $("#totalCount").textContent = String(total);
  $("#priorityCount").textContent = String(radarState.signals.filter((item) => item.priority === "A").length);
  $("#selectedCount").textContent = String(selected);
  $("#healthySourceCount").textContent = `${radarState.sourceHealth.healthy}/${radarState.sourceHealth.total}正常`;
  $("#sourceStatus").textContent = `${radarState.sourceHealth.healthy}/${radarState.sourceHealth.total} 源正常`;
  $("#updatedAt").textContent = formatTime(updatedAt || new Date().toISOString());
  $("#briefDate").textContent = formatDate(updatedAt || radarState.updatedAt);
  $("#radarSubtitle").textContent = `每日简报 · ${formatDate(updatedAt || radarState.updatedAt)} · ${total} 条信号 · ${radarState.signals.filter((item) => item.priority === "A").length} 条高优先级`;
}

function categoryCount(categoryId) {
  if (categoryId === "hot") return radarState.signals.length || fallbackSignals.length;
  return radarState.signals.filter((item) => item.category === categoryId).length;
}

function renderSignals() {
  const items = filteredSignals();
  $("#resultMeta").textContent = `行业信号 · ${items.length || 0} 条`;
  $("#filterMeta").textContent = `${items.length || 0} 条结果 · ${radarState.sourceHealth.healthy}/${radarState.sourceHealth.total} 源正常`;
  $("#signalGrid").innerHTML = items.length
    ? renderSignalGroups(items)
    : `<article class="signal-card"><h3>没有匹配的资讯</h3><p>换一个关键词，或切回热点分类。</p></article>`;
}

function renderSignalGroups(items) {
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
        <section class="brief-group">
          <div class="brief-group-head">
            <h3>${categoryIcon(group.id)} ${escapeHtml(group.label)}</h3>
            <span>每日简报 · ${escapeHtml(formatDate(radarState.updatedAt))} · ${group.items.length} 条</span>
          </div>
          <div class="brief-list">${group.items.map(renderSignalCard).join("")}</div>
        </section>
      `,
    )
    .join("");
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
  const sourceLink = item.url
    ? `<a href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">查看原文</a>`
    : `<span class="source-unavailable">暂无原文链接</span>`;
  return `
    <article class="signal-card">
      <span class="brief-rank">${String(item.rank).padStart(2, "0")}</span>
      ${renderBriefVisual(item)}
      <div class="brief-copy">
        <button type="button" class="brief-title" data-open-detail="${escapeHtml(item.id)}">${escapeHtml(item.title)}</button>
        <p>${escapeHtml(item.summary)}</p>
        <div class="signal-meta">
          <em class="${priorityClass}">优先级 ${escapeHtml(item.priority)}</em>
          <small>${escapeHtml(item.source)}</small>
          <small>${escapeHtml(formatDate(item.publishedAt || item.updatedAt))}</small>
          <small>${escapeHtml((item.tags || []).slice(0, 2).join(" / "))}</small>
        </div>
      </div>
      <div class="brief-action">
        ${sourceLink}
      </div>
    </article>
  `;
}

function renderBriefVisual(item) {
  if (item.imageUrl) {
    return `<img class="brief-thumb has-image" src="${escapeHtml(item.imageUrl)}" alt="" loading="lazy" />`;
  }
  return `<div class="brief-thumb is-icon tone-${escapeHtml(item.category)}" aria-hidden="true">${categoryIcon(item.category)}</div>`;
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

// ═══════════════════════════════════════
// 工具函数
// ═══════════════════════════════════════

function formatTime(value) {
  const date = value ? new Date(value) : new Date();
  if (Number.isNaN(date.getTime())) return "06/30 08:03";
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hour = String(date.getHours()).padStart(2, "0");
  const minute = String(date.getMinutes()).padStart(2, "0");
  return `${month}/${day} ${hour}:${minute}`;
}

function formatDate(value) {
  const date = value ? new Date(value) : new Date();
  if (Number.isNaN(date.getTime())) return "2026/07/01";
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}/${month}/${day}`;
}

function categoryLabel(categoryId) {
  return categories.find((category) => category.id === categoryId)?.label || "行业信号";
}

function categoryIcon(categoryId) {
  const icons = {
    industry: "▣",
    product: "✚",
    research: "§",
    media: "◈",
    community: "◎",
    hot: "◆",
  };
  return icons[categoryId] || "◆";
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
