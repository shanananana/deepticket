import { renderMarkdown } from "/static/markdown.js?v=16";

const ASSET_VERSION = "13";
const TOKEN_KEY = "deepticket_token";
const PROJECT_KEY = "deepticket_project_id";
const RECORD_MODE_KEY = "deepticket_record_mode";

const ACTIVITY_ICONS = {
  log: "📋",
  config: "⚙️",
  code: "📁",
  skill: "🧩",
  search: "🔍",
  terminal: "⌨️",
  think: "💡",
  evidence: "🔎",
  handoff: "✓",
  error: "⚠️",
  system: "◆",
  default: "•",
};

const CONFIDENCE_ANALYSIS_KINDS = new Set([
  "log",
  "config",
  "code",
  "skill",
  "search",
  "terminal",
  "evidence",
  "error",
]);

const ICONS = {
  edit: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4Z"/></svg>',
  trash: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>',
  copy: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>',
  check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
  chevron: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>',
};

/** agents.md 默认模板：选择后填入下方编辑框，用户可再改 */
const AGENTS_MD_TEMPLATES = [
  {
    id: "",
    label: "不注入（空）",
    content: "",
  },
  {
    id: "sre",
    label: "SRE 故障排查",
    content: `你是本项目的 SRE 助手，负责故障定位与根因分析。

工作方式：
- 优先只读检索 workspace 知识库与代码，引用具体文件路径和日志行
- 先复述现象，再给出 1～3 个最可能根因，并说明证据
- 给出可执行的排查步骤与修复建议；不确定处明确标注
- 不要臆造不存在的配置、指标或代码；不要运行破坏性命令`,
  },
  {
    id: "code_qa",
    label: "代码走读 / Q&A",
    content: `你是本项目的代码分析助手。

工作方式：
- 基于 workspace 内代码与文档回答，引用文件路径
- 解释调用链、数据流与关键配置；对比改动影响
- 只读分析，不修改代码，不执行可能写盘或发网的命令
- 回答简洁，先结论后依据`,
  },
  {
    id: "business",
    label: "业务指标分析",
    content: `你是本项目的业务分析助手，擅长从日志、配置与指标中找异常原因。

工作方式：
- 对比时间窗口前后的关键指标（如 ROI、转化率、预算、曝光）
- 结合 campaign / 配置变更日志，给出归因与证据
- 只读查 workspace 中的 .log、yaml、csv 等；不要生成假数据
- 输出：现象摘要 → 根因假设 → 证据 → 建议动作`,
  },
  {
    id: "ticket",
    label: "工单分流",
    content: `你是工单 triage 助手。

工作方式：
- 从标题、描述、日志中提取：影响面、紧急度、可能模块
- 建议路由（研发 / SRE / 业务）与下一步动作
- 需要查代码或配置时，只读检索 workspace
- 回复结构：摘要 / 严重级别 / 建议处理人 / 待办清单`,
  },
];

const AGENTS_MD_CUSTOM_TEMPLATE_ID = "_custom";

/* DOM 引用 */
const $ = (id) => document.getElementById(id);
const userLabel = $("userLabel");
const userAvatar = $("userAvatar");
const menuUserName = $("menuUserName");
const chatListEl = $("chatList");
const chatTitleEl = $("chatTitle");
const messagesEl = $("messages");
const messagesInner = messagesEl.querySelector(".messages-inner");
const emptyStateEl = $("emptyState");
const promptEl = $("prompt");
const chatForm = $("chatForm");
const imageUrlsEl = $("imageUrls");
const sendBtn = $("sendBtn");
const stopBtn = $("stopBtn");
const statusEl = $("status");
const statusPill = $("statusPill");
const modelLabelEl = $("modelLabel");
const knowledgeLabelEl = $("knowledgeLabel");
const storageLabelEl = $("storageLabel");
const conversationIdEl = $("conversationId");
const newChatBtn = $("newChatBtn");
const searchInput = $("searchInput");
const syncKnowledgeBtn = $("syncKnowledgeBtn");
const ticketTemplateBtn = $("ticketTemplateBtn");
const reloadSkillsBtn = $("reloadSkillsBtn");
const recordModeBtn = $("recordModeBtn");
const logoutBtn = $("logoutBtn");
const settingsBtn = $("settingsBtn");
const settingsMenu = $("settingsMenu");
const userChipBtn = $("userChipBtn");
const userMenu = $("userMenu");
const sidebar = $("sidebar");
const scrim = $("scrim");
const menuToggle = $("menuToggle");
const toastStack = $("toastStack");
const adminBoardBtn = $("adminBoardBtn");
const adminDashboard = $("adminDashboard");
const adminProjectPanel = $("adminProjectPanel");
const adminProjectsBtn = $("adminProjectsBtn");
const tokenSummary = $("tokenSummary");
const tokenConversations = $("tokenConversations");
const tokenRuns = $("tokenRuns");
const refreshDashboardBtn = $("refreshDashboardBtn");
const closeDashboardBtn = $("closeDashboardBtn");
const closeProjectAdminBtn = $("closeProjectAdminBtn");
const projectSelectEl = $("projectSelect");
const projectConfigPanel = $("projectConfigPanel");
const projectConfigSelect = $("projectConfigSelect");
const projectCreatePanel = $("projectCreatePanel");
const createProjectBtn = $("createProjectBtn");
const cancelCreateProjectBtn = $("cancelCreateProjectBtn");
const submitCreateProjectBtn = $("submitCreateProjectBtn");
const newProjectId = $("newProjectId");
const newProjectName = $("newProjectName");
const newProjectDescription = $("newProjectDescription");
const projectMembersTags = $("projectMembersTags");
const projectMembersEditor = $("projectMembersEditor");
const saveProjectMembersBtn = $("saveProjectMembersBtn");
const projectConfigHint = $("projectConfigHint");
const projectMetaName = $("projectMetaName");
const projectMetaDescription = $("projectMetaDescription");
const projectMetaEnabled = $("projectMetaEnabled");
const projectReposEditor = $("projectReposEditor");
const projectMcpEditor = $("projectMcpEditor");
const projectAgentsTemplate = $("projectAgentsTemplate");
const projectAgentsEditor = $("projectAgentsEditor");
const saveProjectMetaBtn = $("saveProjectMetaBtn");
const loadProjectMetaDefaultBtn = $("loadProjectMetaDefaultBtn");
const saveProjectReposBtn = $("saveProjectReposBtn");
const loadProjectReposDefaultBtn = $("loadProjectReposDefaultBtn");
const saveProjectMcpBtn = $("saveProjectMcpBtn");
const loadProjectMcpDefaultBtn = $("loadProjectMcpDefaultBtn");
const saveProjectAgentsBtn = $("saveProjectAgentsBtn");
const loadProjectAgentsDefaultBtn = $("loadProjectAgentsDefaultBtn");
const reloadProjectConfigBtn = $("reloadProjectConfigBtn");
const composerZone = document.querySelector(".composer-zone");

/* 状态 */
let authToken = localStorage.getItem(TOKEN_KEY) || "";
let currentUser = null;
let isAdmin = false;
let adminViewMode = null;
let dashboardPollTimer = null;
let currentChatId = null;
let agentConversationId = null;
let busy = false;
let chatAbortController = null;
let allChats = [];
let availableProjects = [];
let currentProjectId = localStorage.getItem(PROJECT_KEY) || "default";
let adminProjectYamlDefaults = null;
let recordMode = localStorage.getItem(RECORD_MODE_KEY) === "1";

function projectQuery(extra = "") {
  const join = extra.includes("?") ? "&" : "?";
  return `${extra}${join}project_id=${encodeURIComponent(currentProjectId || "default")}`;
}

async function loadProjects() {
  const resp = await apiFetch("/api/projects");
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.detail || "加载项目失败");
  availableProjects = data.projects || [];
  if (!availableProjects.some((item) => item.id === currentProjectId)) {
    currentProjectId = availableProjects[0]?.id || "default";
    localStorage.setItem(PROJECT_KEY, currentProjectId);
  }
  if (projectSelectEl) {
    projectSelectEl.innerHTML = availableProjects
      .map(
        (item) =>
          `<option value="${escapeHtml(item.id)}"${item.id === currentProjectId ? " selected" : ""}>${escapeHtml(item.name)} (${escapeHtml(item.id)})</option>`,
      )
      .join("");
  }
}

async function switchProject(projectId) {
  if (!projectId || projectId === currentProjectId) return;
  currentProjectId = projectId;
  localStorage.setItem(PROJECT_KEY, currentProjectId);
  currentChatId = null;
  agentConversationId = null;
  clearChatPanel();
  await loadHealth();
  await refreshChats();
}

function syncRecordModeUi() {
  if (!recordModeBtn) return;
  recordModeBtn.classList.toggle("active", recordMode);
  recordModeBtn.setAttribute("aria-pressed", recordMode ? "true" : "false");
}

syncRecordModeUi();

if (!authToken) window.location.replace("/");

/* --------------------------------------------------------------------------
 * 工具
 * ------------------------------------------------------------------------ */

function authHeaders(extra = {}) {
  const headers = { ...extra };
  if (authToken) headers.Authorization = `Bearer ${authToken}`;
  return headers;
}

async function apiFetch(url, options = {}) {
  const resp = await fetch(url, {
    ...options,
    headers: authHeaders(options.headers || {}),
  });
  if (resp.status === 401) {
    localStorage.removeItem(TOKEN_KEY);
    window.location.replace("/");
    throw new Error("登录已过期");
  }
  return resp;
}

function toast(message, type = "info", duration = 2600) {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.innerHTML = `<span class="toast-dot"></span><span>${escapeHtml(message)}</span>`;
  toastStack.appendChild(el);
  window.setTimeout(() => {
    el.classList.add("out");
    el.addEventListener("animationend", () => el.remove(), { once: true });
  }, duration);
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function timeAgo(iso) {
  if (!iso) return "";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const diff = Date.now() - then;
  const min = Math.floor(diff / 60000);
  if (min < 1) return "刚刚";
  if (min < 60) return `${min} 分钟前`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr} 小时前`;
  const day = Math.floor(hr / 24);
  if (day < 30) return `${day} 天前`;
  return new Date(then).toLocaleDateString("zh-CN");
}

async function copyText(text, btn) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const ta = document.createElement("textarea");
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    ta.remove();
  }
  if (btn) {
    const orig = btn.innerHTML;
    btn.innerHTML = ICONS.check;
    btn.style.color = "var(--success)";
    window.setTimeout(() => {
      btn.innerHTML = orig;
      btn.style.color = "";
    }, 1300);
  }
}

/* --------------------------------------------------------------------------
 * 状态展示
 * ------------------------------------------------------------------------ */

function setStatus(text, mode = "ready") {
  statusEl.textContent = text;
  statusPill.classList.remove("ready", "busy", "error");
  statusPill.classList.add(mode === "busy" ? "busy" : mode === "error" ? "error" : "ready");
}

function setBusy(nextBusy) {
  busy = nextBusy;
  sendBtn.disabled = nextBusy || !currentChatId;
  stopBtn.classList.toggle("hidden", !nextBusy);
  newChatBtn.disabled = nextBusy;
}

function setComposerEnabled(enabled) {
  promptEl.disabled = !enabled;
  if (imageUrlsEl) imageUrlsEl.disabled = !enabled;
  sendBtn.disabled = !enabled || busy;
}

function updateEmptyState() {
  const hasMessages = messagesInner.querySelector(".msg");
  emptyStateEl.style.display = hasMessages ? "none" : "";
}

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function updateConversationMeta() {
  conversationIdEl.textContent = agentConversationId
    ? `Agent · ${agentConversationId.slice(0, 12)}…`
    : "";
}

function autoResizePrompt() {
  promptEl.style.height = "auto";
  promptEl.style.height = `${Math.min(promptEl.scrollHeight, 200)}px`;
}

/* --------------------------------------------------------------------------
 * 消息渲染
 * ------------------------------------------------------------------------ */

function createMessageRow(role) {
  const row = document.createElement("div");
  row.className = `msg ${role}`;
  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.textContent = role === "user" ? (currentUser?.username?.[0] || "U").toUpperCase() : "AI";
  const body = document.createElement("div");
  body.className = "msg-body";
  const content = document.createElement("div");
  content.className = "msg-content";
  body.appendChild(content);
  row.appendChild(avatar);
  row.appendChild(body);
  messagesInner.appendChild(row);
  updateEmptyState();
  scrollToBottom();
  return { row, body, content };
}

function addUserMessage(text) {
  createMessageRow("user").content.textContent = text;
  scrollToBottom();
}

function addToolbar(body, rawText) {
  const bar = document.createElement("div");
  bar.className = "msg-toolbar";
  const copyBtn = document.createElement("button");
  copyBtn.type = "button";
  copyBtn.className = "icon-btn";
  copyBtn.title = "复制";
  copyBtn.innerHTML = ICONS.copy;
  copyBtn.addEventListener("click", () => copyText(rawText, copyBtn));
  bar.appendChild(copyBtn);
  body.appendChild(bar);
}

function shouldShowConfidence(confidence, activities) {
  if (!confidence || confidence.score == null) return false;
  if (confidence.applicable === false) return false;
  if (Array.isArray(activities) && activities.length) {
    return activities.some((item) => CONFIDENCE_ANALYSIS_KINDS.has(item.kind || "default"));
  }
  return confidence.applicable === true;
}

function renderConfidenceBadge(confidence) {
  if (!confidence || confidence.score == null) return null;
  const badge = document.createElement("div");
  const level = confidence.level || "medium";
  badge.className = `confidence-badge confidence-${level}`;
  const reasons = Array.isArray(confidence.reasons) ? confidence.reasons : [];
  if (reasons.length) badge.title = reasons.join("\n");
  badge.innerHTML = `<span class="confidence-label">置信度</span><strong>${escapeHtml(confidence.label || "—")}</strong><span class="confidence-score">${confidence.score}%</span>`;
  return badge;
}

function attachConfidence(body, confidence, activities = null) {
  const existing = body.querySelector(".confidence-badge");
  if (existing) existing.remove();
  if (!shouldShowConfidence(confidence, activities)) return;
  const badge = renderConfidenceBadge(confidence);
  if (badge) body.appendChild(badge);
}

function createAssistantShell(withThinking, options = {}) {
  const { row, body, content } = createMessageRow("assistant");
  let thinking = null;
  if (withThinking) {
    thinking = createThinkingBlock(options);
    body.insertBefore(thinking.root, content);
    scrollToBottom();
  }
  return { row, body, content, thinking };
}

function bindCodeCopy(container) {
  container.querySelectorAll(".md-copy").forEach((btn) => {
    btn.addEventListener("click", () => {
      const pre = btn.closest(".md-pre");
      const raw = pre?.dataset.code ?? pre?.querySelector("code")?.textContent ?? "";
      copyText(raw, null);
      const orig = btn.textContent;
      btn.textContent = "已复制";
      btn.classList.add("ok");
      window.setTimeout(() => {
        btn.textContent = orig;
        btn.classList.remove("ok");
      }, 1300);
    });
  });
}

/* Thinking 块 — 展示 Agent 实时活动（来自 SSE activity 事件） */

function createThinkingStepEl(item, { isLast, iconFor }) {
  const step = document.createElement("div");
  step.className = "thinking-step";
  if (item.kind === "evidence") step.classList.add("evidence");
  if (item.kind === "handoff") step.classList.add("handoff");
  if (item.kind === "error") step.classList.add("error");
  step.classList.add(isLast ? "current" : "done");
  step.innerHTML = `<span class="step-icon">${iconFor(item.kind)}</span><span class="step-text">${escapeHtml(item.text)}</span>`;
  return step;
}

function updateThinkingScrollState(bodyEl, tabScrollEl) {
  if (bodyEl) {
    const { scrollTop, scrollHeight, clientHeight } = bodyEl;
    bodyEl.classList.toggle("can-scroll-top", scrollTop > 6);
    bodyEl.classList.toggle("can-scroll-bottom", scrollTop + clientHeight < scrollHeight - 6);
  }
  if (tabScrollEl) {
    const { scrollLeft, scrollWidth, clientWidth } = tabScrollEl;
    tabScrollEl.classList.toggle("can-scroll-end", scrollLeft + clientWidth < scrollWidth - 6);
  }
}

function scrollThinkingPanel({ bodyEl, tabScrollEl, stickBody = true }) {
  if (bodyEl && stickBody) {
    bodyEl.scrollTop = bodyEl.scrollHeight;
  }
  if (tabScrollEl) {
    tabScrollEl.scrollLeft = tabScrollEl.scrollWidth;
  }
  updateThinkingScrollState(bodyEl, tabScrollEl);
}

function bindThinkingInteractions(root, { bodyEl, tabScrollEl, toggleEl }) {
  let stickBody = true;
  let tabDragged = false;
  let tabDragStartX = 0;

  bodyEl.addEventListener(
    "scroll",
    () => {
      stickBody = bodyEl.scrollHeight - bodyEl.scrollTop - bodyEl.clientHeight < 28;
      updateThinkingScrollState(bodyEl, tabScrollEl);
    },
    { passive: true },
  );

  tabScrollEl.addEventListener(
    "scroll",
    () => updateThinkingScrollState(bodyEl, tabScrollEl),
    { passive: true },
  );

  tabScrollEl.addEventListener("wheel", (event) => {
    if (Math.abs(event.deltaY) <= Math.abs(event.deltaX)) return;
    event.preventDefault();
    tabScrollEl.scrollLeft += event.deltaY;
  }, { passive: false });

  tabScrollEl.addEventListener("pointerdown", (event) => {
    tabDragStartX = event.clientX;
    tabDragged = false;
  });

  tabScrollEl.addEventListener("pointermove", (event) => {
    if (Math.abs(event.clientX - tabDragStartX) > 8) tabDragged = true;
  });

  toggleEl.addEventListener("click", (event) => {
    if (tabDragged && event.target.closest(".thinking-tab-scroll")) {
      event.preventDefault();
      tabDragged = false;
      return;
    }
    root.classList.toggle("collapsed");
    if (!root.classList.contains("collapsed")) {
      requestAnimationFrame(() => scrollThinkingPanel({ bodyEl, tabScrollEl, stickBody: true }));
    }
  });

  return {
    shouldStickBody: () => stickBody,
    resetStickBody: () => {
      stickBody = true;
    },
  };
}

function syncThinkingSteps(stepsEl, activities, iconFor, { markLastCurrent = true } = {}) {
  const iconFn = iconFor;
  if (!activities.length) {
    stepsEl.innerHTML = `<div class="thinking-step current"><span class="step-icon">${iconFn("system")}</span><span class="step-text">等待 Agent 响应…</span></div>`;
    return;
  }

  while (stepsEl.children.length > activities.length) {
    stepsEl.lastElementChild?.remove();
  }

  activities.forEach((item, idx) => {
    const isLast = idx === activities.length - 1;
    let step = stepsEl.children[idx];
    if (!step) {
      step = createThinkingStepEl(item, { isLast: isLast && markLastCurrent, iconFor: iconFn });
      stepsEl.appendChild(step);
      return;
    }
    step.className = "thinking-step";
    if (item.kind === "evidence") step.classList.add("evidence");
    if (item.kind === "handoff") step.classList.add("handoff");
    if (item.kind === "error") step.classList.add("error");
    step.classList.add(isLast && markLastCurrent ? "current" : "done");
    const textEl = step.querySelector(".step-text");
    if (textEl && textEl.textContent !== item.text) {
      textEl.textContent = item.text;
    }
    const iconEl = step.querySelector(".step-icon");
    if (iconEl) iconEl.textContent = iconFn(item.kind);
  });
}

function buildThinkingShell({ keepExpanded = false, label = "正在准备", showElapsed = true } = {}) {
  const root = document.createElement("div");
  root.className = "thinking active";
  if (keepExpanded) root.classList.add("record-mode");
  root.innerHTML = `
    <button type="button" class="thinking-toggle">
      <span class="thinking-spinner"></span>
      <span class="thinking-check">✓</span>
      <div class="thinking-tab-scroll" aria-label="思考步骤摘要">
        <span class="thinking-label">${escapeHtml(label)}</span>
      </div>
      <span class="thinking-step-count"></span>
      ${showElapsed ? '<span class="thinking-elapsed">0s</span>' : ""}
      <span class="thinking-chevron">${ICONS.chevron}</span>
    </button>
    <div class="thinking-body">
      <div class="thinking-steps"></div>
      <div class="thinking-shimmer"></div>
    </div>
  `;

  const toggleEl = root.querySelector(".thinking-toggle");
  const bodyEl = root.querySelector(".thinking-body");
  const tabScrollEl = root.querySelector(".thinking-tab-scroll");
  const stepsEl = root.querySelector(".thinking-steps");
  const labelEl = root.querySelector(".thinking-label");
  const countEl = root.querySelector(".thinking-step-count");
  const elapsedEl = root.querySelector(".thinking-elapsed");
  const interaction = bindThinkingInteractions(root, { bodyEl, tabScrollEl, toggleEl });

  return { root, toggleEl, bodyEl, tabScrollEl, stepsEl, labelEl, countEl, elapsedEl, interaction };
}

function createThinkingBlock(options = {}) {
  const keepExpanded = Boolean(options.recordMode);
  const {
    root,
    bodyEl,
    tabScrollEl,
    stepsEl,
    labelEl,
    countEl,
    elapsedEl,
    interaction,
  } = buildThinkingShell({ keepExpanded, label: "正在准备", showElapsed: true });

  const activities = [];
  let currentActivity = "";
  let currentKind = "default";

  const iconFor = (kind) => ACTIVITY_ICONS[kind] || ACTIVITY_ICONS.default;

  const renderSteps = () => {
    syncThinkingSteps(stepsEl, activities, iconFor);
    if (countEl) {
      countEl.textContent = activities.length ? String(activities.length) : "";
      countEl.classList.toggle("visible", activities.length > 1);
    }
    scrollThinkingPanel({
      bodyEl,
      tabScrollEl,
      stickBody: interaction.shouldStickBody(),
    });
    scrollToBottom();
  };

  const startedAt = Date.now();
  const elapsedTimer = window.setInterval(() => {
    if (!elapsedEl) return;
    elapsedEl.textContent = `${Math.max(1, Math.round((Date.now() - startedAt) / 1000))}s`;
  }, 250);

  renderSteps();

  return {
    root,
    addActivity(text, kind = "default") {
      const next = (text || "").trim();
      if (!next || (next === currentActivity && kind === currentKind)) return;
      currentActivity = next;
      currentKind = kind;
      const last = activities[activities.length - 1];
      if (!last || last.text !== next || last.kind !== kind) {
        activities.push({ text: next, kind });
      }
      labelEl.textContent = next;
      renderSteps();
    },
    markReplyStarting() {
      this.addActivity("已获取到所有信息，开始回复", "handoff");
    },
    finish(contentStarted = false) {
      window.clearInterval(elapsedTimer);
      const seconds = Math.max(1, Math.round((Date.now() - startedAt) / 1000));
      if (elapsedEl) elapsedEl.textContent = `${seconds}s`;
      root.classList.remove("active");
      root.classList.add("done");
      stepsEl.querySelectorAll(".thinking-step").forEach((el) => {
        el.classList.remove("current");
        el.classList.add("done");
      });
      root.querySelector(".thinking-shimmer")?.remove();
      const stepCount = activities.length;
      if (contentStarted) {
        labelEl.textContent = stepCount
          ? `思考完成 · ${stepCount} 步 · ${seconds}s`
          : `思考用时 ${seconds}s`;
      } else {
        labelEl.textContent = stepCount
          ? `运行完成 · ${stepCount} 步 · ${seconds}s`
          : `运行 ${seconds}s`;
      }
      if (countEl) {
        countEl.textContent = stepCount ? String(stepCount) : "";
        countEl.classList.toggle("visible", stepCount > 1);
      }
      scrollThinkingPanel({ bodyEl, tabScrollEl, stickBody: true });
      if (!keepExpanded) {
        window.setTimeout(() => root.classList.add("collapsed"), contentStarted ? 2500 : 4000);
      }
    },
    stop() {
      window.clearInterval(elapsedTimer);
    },
  };
}

function createStaticThinkingBlock(activities) {
  const safeActivities = Array.isArray(activities) ? activities : [];
  const { root, bodyEl, tabScrollEl, stepsEl, labelEl, countEl } = buildThinkingShell({
    keepExpanded: false,
    label: `Agent 步骤（${safeActivities.length}）`,
    showElapsed: false,
  });

  root.className = "thinking done collapsed";
  const iconFor = (kind) => ACTIVITY_ICONS[kind] || ACTIVITY_ICONS.default;
  syncThinkingSteps(stepsEl, safeActivities, iconFor, { markLastCurrent: false });
  if (countEl) {
    countEl.textContent = safeActivities.length ? String(safeActivities.length) : "";
    countEl.classList.toggle("visible", safeActivities.length > 1);
  }
  requestAnimationFrame(() => scrollThinkingPanel({ bodyEl, tabScrollEl, stickBody: false }));
  return root;
}

function renderHistory(messages) {
  messagesInner.querySelectorAll(".msg").forEach((el) => el.remove());
  for (const item of messages || []) {
    if (item.role === "user") {
      addUserMessage(item.content);
    } else if (item.role === "assistant") {
      const { body, content } = createAssistantShell(false);
      if (Array.isArray(item.activities) && item.activities.length) {
        body.insertBefore(createStaticThinkingBlock(item.activities), content);
      }
      content.innerHTML = renderMarkdown(item.content);
      bindCodeCopy(content);
      addToolbar(body, item.content);
      attachConfidence(body, item.confidence, item.activities);
    }
  }
  updateEmptyState();
  scrollToBottom();
}

function clearChatPanel() {
  currentChatId = null;
  agentConversationId = null;
  chatTitleEl.textContent = "选择或新建对话";
  updateConversationMeta();
  messagesInner.querySelectorAll(".msg").forEach((el) => el.remove());
  updateEmptyState();
  setComposerEnabled(false);
  renderChatList();
}

/* --------------------------------------------------------------------------
 * 会话列表
 * ------------------------------------------------------------------------ */

function renderChatList() {
  const query = searchInput.value.trim().toLowerCase();
  const visible = query
    ? allChats.filter((c) => {
        const title = (c.title || "").toLowerCase();
        const blob = (c.search_text || "").toLowerCase();
        return title.includes(query) || blob.includes(query);
      })
    : allChats;

  chatListEl.innerHTML = "";
  if (!allChats.length) {
    chatListEl.innerHTML = '<div class="chat-list-empty">暂无对话<br />点击上方「新对话」开始</div>';
    return;
  }
  if (!visible.length) {
    chatListEl.innerHTML = '<div class="chat-list-empty">没有匹配的对话</div>';
    return;
  }

  for (const chat of visible) {
    const item = document.createElement("div");
    item.className = "chat-item";
    if (chat.chat_id === currentChatId) item.classList.add("active");
    item.dataset.chatId = chat.chat_id;

    const body = document.createElement("div");
    body.className = "chat-item-body";
    const title = document.createElement("span");
    title.className = "chat-item-title";
    title.textContent = chat.title || "新会话";
    const time = document.createElement("span");
    time.className = "chat-item-time";
    time.textContent = timeAgo(chat.updated_at);
    body.appendChild(title);
    body.appendChild(time);

    const actions = document.createElement("div");
    actions.className = "chat-item-actions";

    const renameBtn = document.createElement("button");
    renameBtn.type = "button";
    renameBtn.className = "icon-btn";
    renameBtn.title = "重命名";
    renameBtn.innerHTML = ICONS.edit;
    renameBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      startRename(item, chat, title);
    });

    const delBtn = document.createElement("button");
    delBtn.type = "button";
    delBtn.className = "icon-btn danger";
    delBtn.title = "删除";
    delBtn.innerHTML = ICONS.trash;
    delBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      confirmDelete(chat.chat_id);
    });

    actions.appendChild(renameBtn);
    actions.appendChild(delBtn);
    item.appendChild(body);
    item.appendChild(actions);
    item.addEventListener("click", () => openChat(chat.chat_id));
    chatListEl.appendChild(item);
  }
}

function startRename(item, chat, titleEl) {
  const input = document.createElement("input");
  input.type = "text";
  input.className = "chat-rename-input";
  input.value = chat.title || "新会话";
  titleEl.replaceWith(input);
  input.focus();
  input.select();

  let done = false;
  async function commit(save) {
    if (done) return;
    done = true;
    const next = input.value.trim();
    if (save && next && next !== chat.title) {
      try {
        const resp = await apiFetch(projectQuery(`/api/chats/${chat.chat_id}`), {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: next }),
        });
        if (resp.ok) {
          chat.title = next;
          if (currentChatId === chat.chat_id) chatTitleEl.textContent = next;
          toast("已重命名", "success");
        } else {
          toast("重命名失败", "error");
        }
      } catch {
        toast("重命名失败", "error");
      }
    }
    await refreshChats();
  }

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") commit(true);
    if (e.key === "Escape") commit(false);
    e.stopPropagation();
  });
  input.addEventListener("blur", () => commit(true));
  input.addEventListener("click", (e) => e.stopPropagation());
}

async function confirmDelete(chatId) {
  const chat = allChats.find((c) => c.chat_id === chatId);
  if (!window.confirm(`删除对话「${chat?.title || "新会话"}」？此操作不可撤销。`)) return;
  try {
    const resp = await apiFetch(projectQuery(`/api/chats/${chatId}`), { method: "DELETE" });
    if (!resp.ok) throw new Error();
    allChats = allChats.filter((c) => c.chat_id !== chatId);
    if (currentChatId === chatId) clearChatPanel();
    else renderChatList();
    toast("已删除", "success");
  } catch {
    toast("删除失败", "error");
  }
}

async function refreshChats() {
  const resp = await apiFetch(projectQuery("/api/chats"));
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.detail || "加载对话失败");
  allChats = data.chats || [];
  renderChatList();
}

/* --------------------------------------------------------------------------
 * 会话打开 / 创建
 * ------------------------------------------------------------------------ */

async function openChat(chatId) {
  if (busy) return;
  if (adminViewMode) {
    closeAdminView({ restoreChat: false });
  }
  const resp = await apiFetch(projectQuery(`/api/chats/${chatId}`));
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.detail || "打开对话失败");

  currentChatId = data.chat.chat_id;
  agentConversationId = data.chat.agent_conversation_id || null;
  chatTitleEl.textContent = data.chat.title || "新会话";
  renderHistory(data.chat.messages || []);
  updateConversationMeta();
  setComposerEnabled(true);
  renderChatList();
  setStatus("就绪");
  closeSidebarMobile();
  promptEl.focus();
  resumePendingAssistant(data.chat).catch((err) => toast(err.message, "error"));
}

async function createChat() {
  if (busy) return;
  if (chatAbortController) {
    chatAbortController.abort();
    chatAbortController = null;
  }
  const resp = await apiFetch("/api/chats", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: "新会话", project_id: currentProjectId }),
  });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.detail || "创建对话失败");
  await refreshChats();
  await openChat(data.chat.chat_id);
}

/* --------------------------------------------------------------------------
 * 发送消息（流式 + Markdown 增量渲染）
 * ------------------------------------------------------------------------ */

async function pollChatForReply(chatId, baselineCount, { maxAttempts = 15 } = {}) {
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    await new Promise((resolve) => window.setTimeout(resolve, 2000));
    const resp = await apiFetch(projectQuery(`/api/chats/${chatId}`));
    const data = await resp.json();
    if (!resp.ok) continue;
    const chat = data.chat || {};
    const messages = chat.messages || [];
    if (messages.length > baselineCount) {
      const last = messages[messages.length - 1];
      if (last?.role === "assistant" && last.content) return { chat, message: last };
    }
    if (chat.agent_run_status === "failed") return { chat, message: null };
    if (chat.agent_run_status === "idle" && messages.length > baselineCount) {
      const last = messages[messages.length - 1];
      if (last?.role === "assistant") return { chat, message: last };
    }
  }
  return null;
}

function chatNeedsAssistantWait(chat) {
  const messages = chat?.messages || [];
  if (!messages.length) return false;
  const last = messages[messages.length - 1];
  return last.role === "user" && chat.agent_run_status === "running";
}

async function waitForAssistantReply(chatId, baselineCount) {
  const result = await pollChatForReply(chatId, baselineCount, { maxAttempts: 90 });
  return result?.chat || null;
}

async function resumePendingAssistant(chat) {
  if (!chatNeedsAssistantWait(chat)) return;
  const baselineCount = (chat.messages || []).length;
  setBusy(true);
  setStatus("Agent 仍在分析…", "busy");
  const { body, content, thinking } = createAssistantShell(true, { recordMode });
  content.classList.add("placeholder");
  content.textContent = "Agent 仍在后台分析，等待回复…";
  thinking.addActivity("已重新连接对话，等待 Agent 完成…", "system");
  try {
    const updated = await waitForAssistantReply(chat.chat_id, baselineCount);
    if (!updated || currentChatId !== chat.chat_id) return;
    renderHistory(updated.messages || []);
    await refreshChats();
    if (updated.title) chatTitleEl.textContent = updated.title;
    setStatus("就绪");
    toast("回复已就绪", "success");
  } catch (err) {
    toast(err.message || "等待回复失败", "error");
    setStatus("就绪");
  } finally {
    setBusy(false);
  }
}

function parseImageUrls(raw) {
  return raw
    .split(/[\n,]+/)
    .map((item) => item.trim())
    .filter((item) => /^https?:\/\//i.test(item));
}

let userStoppedRun = false;

async function sendMessage(text) {
  const message = text.trim();
  if (!message || busy || !currentChatId) return;

  const imageUrls = imageUrlsEl ? parseImageUrls(imageUrlsEl.value || "") : [];
  let baselineCount = 0;
  try {
    const baselineResp = await apiFetch(projectQuery(`/api/chats/${currentChatId}`));
    const baselineData = await baselineResp.json();
    if (baselineResp.ok) {
      baselineCount = (baselineData.chat?.messages || []).length;
    }
  } catch {
    baselineCount = 0;
  }

  setBusy(true);
  setStatus("正在思考…", "busy");
  addUserMessage(message);

  const { body, content, thinking } = createAssistantShell(true, { recordMode });
  content.classList.add("placeholder");
  content.textContent = "等待 Agent 响应…";
  thinking.addActivity("问题已提交，正在连接 Agent…", "system");

  chatAbortController = new AbortController();
  const { signal } = chatAbortController;

  let assistantText = "";
  let contentStarted = false;
  let renderScheduled = false;
  let latestConfidence = null;
  const chatActivities = [];

  const flushRender = () => {
    renderScheduled = false;
    const streaming = content.classList.contains("streaming");
    content.innerHTML = renderMarkdown(assistantText, { streaming });
    if (!streaming) bindCodeCopy(content);
    scrollToBottom();
  };

  const scheduleRender = () => {
    if (!renderScheduled) {
      renderScheduled = true;
      requestAnimationFrame(flushRender);
    }
  };

  const fail = (msg) => {
    thinking.finish(contentStarted);
    content.className = "msg-error";
    content.textContent = msg;
    setStatus("失败", "error");
  };

  try {
    const resp = await apiFetch(projectQuery("/api/chat"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        chat_id: currentChatId,
        conversation_id: agentConversationId,
        image_urls: imageUrls,
      }),
      signal,
    });

    if (!resp.ok) {
      const detail = await resp.text();
      fail(detail || "请求失败");
      return;
    }

    const headerConv = resp.headers.get("X-OpenHands-ServerConversation-ID");
    if (headerConv) {
      agentConversationId = headerConv;
      updateConversationMeta();
    }

    setStatus("生成回复中…", "busy");

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    for (;;) {
      if (signal.aborted) {
        await reader.cancel();
        thinking.stop();
        if (userStoppedRun) {
          setStatus("已停止", "error");
        } else {
          setStatus("连接已断开，Agent 仍在后台分析…", "busy");
          const activeChatId = currentChatId;
          pollChatForReply(activeChatId, baselineCount, { maxAttempts: 90 })
            .then((result) => {
              if (!result?.message || currentChatId !== activeChatId) return;
              renderHistory(result.chat.messages || []);
              refreshChats().catch(() => {});
              setStatus("已从服务端恢复回复", "ready");
              toast("回复已就绪", "success");
            })
            .catch(() => {});
        }
        return;
      }
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() || "";

      for (const part of parts) {
        if (part.startsWith("event: ping")) {
          continue;
        }
        if (part.startsWith("event: activity")) {
          const line = part.split("\n").find((l) => l.startsWith("data: "));
          if (line) {
            try {
              const meta = JSON.parse(line.slice(6));
              if (meta.activity) {
                const kind = meta.kind || "default";
                chatActivities.push({ text: meta.activity, kind });
                thinking.addActivity(meta.activity, kind);
                if (kind === "error") setStatus("Agent 异常", "error");
                scrollToBottom();
                await new Promise((resolve) => requestAnimationFrame(resolve));
              }
            } catch { /* 忽略 */ }
          }
          continue;
        }
        if (part.startsWith("event: confidence")) {
          const line = part.split("\n").find((l) => l.startsWith("data: "));
          if (line) {
            try {
              latestConfidence = JSON.parse(line.slice(6));
              attachConfidence(body, latestConfidence, chatActivities);
            } catch { /* 忽略 */ }
          }
          continue;
        }
        if (part.startsWith("event: meta")) {
          const line = part.split("\n").find((l) => l.startsWith("data: "));
          if (line) {
            try {
              const meta = JSON.parse(line.slice(6));
              if (meta.conversation_id) {
                agentConversationId = meta.conversation_id;
                updateConversationMeta();
              }
            } catch { /* 忽略 */ }
          }
          continue;
        }
        const dataLine = part.split("\n").find((l) => l.startsWith("data: "));
        if (!dataLine) continue;
        const payload = dataLine.slice(6).trim();
        if (payload === "[DONE]") continue;
        try {
          const json = JSON.parse(payload);
          if (json.error) {
            fail(json.error);
            return;
          }
          const delta = json.choices?.[0]?.delta?.content;
          if (typeof delta === "string" && delta) {
            if (!contentStarted) {
              contentStarted = true;
              content.classList.remove("placeholder");
              content.classList.add("streaming");
              thinking.markReplyStarting();
              thinking.finish(true);
              setStatus("输出中…", "busy");
            }
            assistantText += delta;
            scheduleRender();
          }
        } catch { /* 忽略格式异常的分片 */ }
      }
    }

    if (renderScheduled) flushRender();
    content.classList.remove("streaming");

    if (!contentStarted) {
      thinking.finish(false);
      content.classList.remove("placeholder");
      content.textContent = "Agent 已完成运行，但未返回文本（可能仅执行了工具）。";
    } else {
      content.innerHTML = renderMarkdown(assistantText);
      bindCodeCopy(content);
      addToolbar(body, assistantText);
      if (latestConfidence) attachConfidence(body, latestConfidence, chatActivities);
    }

    setStatus("就绪");
    if (imageUrlsEl) imageUrlsEl.value = "";
    await refreshChats();
    if (currentChatId) {
      const titleResp = await apiFetch(projectQuery(`/api/chats/${currentChatId}`));
      const titleData = await titleResp.json();
      if (titleResp.ok) chatTitleEl.textContent = titleData.chat.title || "新会话";
    }
  } catch (err) {
    if (err.name === "AbortError") {
      thinking.stop();
      if (userStoppedRun) {
        setStatus("已停止", "error");
      } else {
        setStatus("连接已断开，Agent 仍在后台分析…", "busy");
        const activeChatId = currentChatId;
        pollChatForReply(activeChatId, baselineCount, { maxAttempts: 90 })
          .then((result) => {
            if (!result?.message || currentChatId !== activeChatId) return;
            renderHistory(result.chat.messages || []);
            refreshChats().catch(() => {});
            setStatus("已从服务端恢复回复", "ready");
          })
          .catch(() => {});
      }
      return;
    }
    const recovered = await pollChatForReply(currentChatId, baselineCount);
    if (recovered?.message?.content) {
      thinking.finish(true);
      content.classList.remove("placeholder", "streaming");
      content.innerHTML = renderMarkdown(recovered.message.content);
      bindCodeCopy(content);
      addToolbar(body, recovered.message.content);
      if (Array.isArray(recovered.message.activities) && recovered.message.activities.length) {
        body.insertBefore(createStaticThinkingBlock(recovered.message.activities), content);
      }
      if (recovered.message.confidence) {
        attachConfidence(body, recovered.message.confidence, recovered.message.activities);
      }
      setStatus("已从服务端恢复回复", "ready");
      await refreshChats();
      return;
    }
    fail(err.message);
  } finally {
    userStoppedRun = false;
    chatAbortController = null;
    setBusy(false);
    promptEl.focus();
  }
}

/* --------------------------------------------------------------------------
 * 数据加载
 * ------------------------------------------------------------------------ */

async function loadMe() {
  const resp = await apiFetch("/api/auth/me");
  const data = await resp.json();
  if (!resp.ok) throw new Error("获取用户失败");
  currentUser = data.user;
  isAdmin = Boolean(currentUser.is_admin);
  userLabel.textContent = currentUser.username;
  menuUserName.textContent = currentUser.username;
  userAvatar.textContent = currentUser.username[0].toUpperCase();
  if (adminBoardBtn) adminBoardBtn.classList.toggle("hidden", !isAdmin);
  if (adminProjectsBtn) adminProjectsBtn.classList.toggle("hidden", !isAdmin);
  document.querySelector(".user-role").textContent = isAdmin ? "管理员" : "分析工作台";
  if (syncKnowledgeBtn) syncKnowledgeBtn.classList.toggle("hidden", !isAdmin);
  if (reloadSkillsBtn) reloadSkillsBtn.classList.toggle("hidden", !isAdmin);
}

function formatToken(n) {
  const value = Number(n) || 0;
  return value.toLocaleString("zh-CN");
}

function formatTime(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return escapeHtml(String(value));
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatModel(item) {
  return escapeHtml(item.model_label || item.model || "—");
}

function renderTokenUsage(data) {
  const summary = data.summary || {};
  tokenSummary.innerHTML = `
    <article class="metric-card"><span class="metric-label">Prompt</span><strong>${formatToken(summary.prompt_tokens)}</strong><span class="metric-sub">累计输入</span></article>
    <article class="metric-card"><span class="metric-label">Completion</span><strong>${formatToken(summary.completion_tokens)}</strong><span class="metric-sub">累计输出</span></article>
    <article class="metric-card"><span class="metric-label">Reasoning</span><strong>${formatToken(summary.reasoning_tokens)}</strong><span class="metric-sub">推理 token</span></article>
    <article class="metric-card"><span class="metric-label">Total</span><strong>${formatToken(summary.total_tokens)}</strong><span class="metric-sub">${summary.conversation_count || 0} 个对话</span></article>
  `;

  const conversations = data.conversations || [];
  if (!conversations.length) {
    tokenConversations.innerHTML = '<div class="dashboard-empty">暂无 token 记录，用户发起 Agent 对话后会自动采集</div>';
  } else {
    tokenConversations.innerHTML = `<table class="dashboard-table"><thead><tr><th>用户</th><th>对话</th><th>模型</th><th>Prompt</th><th>Completion</th><th>Reasoning</th><th>Total</th><th>更新时间</th></tr></thead><tbody>${conversations.map((item) => `<tr><td>${escapeHtml(item.username || "—")}</td><td><span class="token-chat-title">${escapeHtml(item.chat_title || "新会话")}</span><code>${escapeHtml(item.chat_id || "")}</code></td><td><span class="token-model-label">${formatModel(item)}</span><code>${escapeHtml(item.model || "")}</code></td><td>${formatToken(item.prompt_tokens)}</td><td>${formatToken(item.completion_tokens)}</td><td>${formatToken(item.reasoning_tokens)}</td><td><strong>${formatToken(item.total_tokens)}</strong></td><td>${formatTime(item.updated_at)}</td></tr>`).join("")}</tbody></table>`;
  }

  const runs = data.runs || [];
  if (!runs.length) {
    tokenRuns.innerHTML = '<div class="dashboard-empty">暂无单次运行记录</div>';
  } else {
    tokenRuns.innerHTML = `<table class="dashboard-table"><thead><tr><th>时间</th><th>用户</th><th>对话</th><th>模型</th><th>本次 Prompt</th><th>本次 Completion</th><th>本次 Reasoning</th><th>本次 Total</th></tr></thead><tbody>${runs.map((item) => `<tr><td>${formatTime(item.recorded_at)}</td><td>${escapeHtml(item.username || "—")}</td><td><span class="token-chat-title">${escapeHtml(item.chat_title || "新会话")}</span><code>${escapeHtml(item.chat_id || "")}</code></td><td><span class="token-model-label">${formatModel(item)}</span><code>${escapeHtml(item.model || "")}</code></td><td>${formatToken(item.prompt_tokens)}</td><td>${formatToken(item.completion_tokens)}</td><td>${formatToken(item.reasoning_tokens)}</td><td><strong>${formatToken(item.total_tokens)}</strong></td></tr>`).join("")}</tbody></table>`;
  }
}

async function loadDashboard() {
  const resp = await apiFetch("/api/admin/token-usage");
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.detail || "加载 Token 消耗失败");
  renderTokenUsage(data);
}

function hideAdminPanels() {
  adminDashboard?.classList.add("hidden");
  adminProjectPanel?.classList.add("hidden");
  if (dashboardPollTimer) {
    window.clearInterval(dashboardPollTimer);
    dashboardPollTimer = null;
  }
}

function enterAdminChrome(title, subtitle) {
  messagesEl.classList.add("hidden");
  if (composerZone) composerZone.classList.add("hidden");
  chatTitleEl.textContent = title;
  conversationIdEl.textContent = subtitle;
  closeSidebarMobile();
}

function updateAdminNavActive() {
  adminBoardBtn?.classList.toggle("active", adminViewMode === "token");
  adminProjectsBtn?.classList.toggle("active", adminViewMode === "projects");
}

function openProjectAdmin() {
  if (!isAdmin) return;
  adminViewMode = "projects";
  hideAdminPanels();
  adminProjectPanel?.classList.remove("hidden");
  toggleCreateProjectPanel(false);
  enterAdminChrome("项目配置", "管理员 · 项目");
  updateAdminNavActive();
  ensureAgentsMdTemplateOptions();
  loadAdminProjectList().catch((err) => toast(err.message, "error"));
}

function ensureAgentsMdTemplateOptions() {
  if (!projectAgentsTemplate || projectAgentsTemplate.dataset.ready === "1") return;
  const options = AGENTS_MD_TEMPLATES.map(
    (item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.label)}</option>`,
  );
  options.push(
    `<option value="${AGENTS_MD_CUSTOM_TEMPLATE_ID}">自定义（保留当前内容）</option>`,
  );
  projectAgentsTemplate.innerHTML = options.join("");
  projectAgentsTemplate.dataset.ready = "1";
}

function agentsMdTemplateContent(templateId) {
  const item = AGENTS_MD_TEMPLATES.find((entry) => entry.id === templateId);
  return item ? item.content : null;
}

function matchAgentsMdTemplateId(content) {
  const normalized = (content || "").trim();
  for (const item of AGENTS_MD_TEMPLATES) {
    if ((item.content || "").trim() === normalized) {
      return item.id;
    }
  }
  return AGENTS_MD_CUSTOM_TEMPLATE_ID;
}

function syncAgentsMdTemplateSelect(content) {
  if (!projectAgentsTemplate) return;
  projectAgentsTemplate.value = matchAgentsMdTemplateId(content);
}

function applyAgentsMdTemplate(templateId) {
  if (templateId === AGENTS_MD_CUSTOM_TEMPLATE_ID) return;
  const content = agentsMdTemplateContent(templateId);
  if (content !== null && projectAgentsEditor) {
    projectAgentsEditor.value = content;
  }
}

async function loadAdminProjectList() {
  const resp = await apiFetch("/api/admin/projects");
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.detail || "加载项目配置失败");
  const projects = data.projects || [];
  if (projectConfigSelect) {
    projectConfigSelect.innerHTML = projects
      .map(
        (item) =>
          `<option value="${escapeHtml(item.id)}">${escapeHtml(item.name)} (${escapeHtml(item.id)})</option>`,
      )
      .join("");
  }
  ensureAgentsMdTemplateOptions();
  const selected = projectConfigSelect?.value || currentProjectId || "default";
  await loadAdminProjectConfig(selected);
}

async function loadAdminProjectConfig(projectId) {
  const resp = await apiFetch(`/api/admin/projects/${encodeURIComponent(projectId)}`);
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.detail || "读取项目配置失败");
  const project = data.project || {};
  const defaults = data.defaults || {};
  adminProjectYamlDefaults = defaults;
  if (projectConfigHint) {
    const source = data.in_redis ? "Redis + yaml 兜底" : "仅 yaml 兜底（尚未写入 Redis）";
    projectConfigHint.textContent = `当前生效：${source}。编辑框显示当前生效值；点「载入 yaml 默认」可单独填入 deepticket.yaml 兜底，改完再保存。`;
  }
  if (projectMetaName) projectMetaName.value = project.name || "";
  if (projectMetaDescription) projectMetaDescription.value = project.description || "";
  if (projectMetaEnabled) projectMetaEnabled.checked = project.enabled !== false;
  if (projectReposEditor) {
    projectReposEditor.value = JSON.stringify(project.knowledge?.repos ?? [], null, 2);
  }
  if (projectMcpEditor) {
    projectMcpEditor.value = JSON.stringify(project.mcp?.servers ?? {}, null, 2);
  }
  if (projectAgentsEditor) {
    const savedAgentsMd = project.extensions?.agents_md ?? "";
    projectAgentsEditor.value = savedAgentsMd;
    syncAgentsMdTemplateSelect(savedAgentsMd);
  }
  renderProjectMembers(data.members || []);
}

function renderProjectMembers(members) {
  if (!projectMembersTags || !projectMembersEditor) return;
  const list = Array.isArray(members) ? members : [];
  if (!list.length) {
    projectMembersTags.classList.add("empty");
    projectMembersTags.innerHTML = "";
  } else {
    projectMembersTags.classList.remove("empty");
    projectMembersTags.innerHTML = list
      .map((item) => `<span class="project-member-tag">${escapeHtml(item.username || item.uid)}</span>`)
      .join("");
  }
  projectMembersEditor.value = list.map((item) => item.username).filter(Boolean).join("\n");
}

function normalizeProjectId(raw) {
  return (raw || "").trim().toLowerCase();
}

function isValidProjectId(projectId) {
  return /^[a-z0-9][a-z0-9_-]{0,63}$/.test(projectId);
}

function toggleCreateProjectPanel(show) {
  if (!projectCreatePanel) return;
  projectCreatePanel.classList.toggle("hidden", !show);
  if (show) {
    if (newProjectId) newProjectId.value = "";
    if (newProjectName) newProjectName.value = "";
    if (newProjectDescription) newProjectDescription.value = "";
    newProjectId?.focus();
  }
}

async function createProject() {
  const projectId = normalizeProjectId(newProjectId?.value);
  const name = (newProjectName?.value || "").trim();
  const description = (newProjectDescription?.value || "").trim();
  if (!isValidProjectId(projectId)) {
    toast("项目 ID 需 1–64 位，小写字母/数字开头，仅含 a-z 0-9 _ -", "error");
    return;
  }
  if (!name) {
    toast("请填写项目名称", "error");
    return;
  }
  const resp = await apiFetch(`/api/admin/projects/${encodeURIComponent(projectId)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      id: projectId,
      name,
      description,
      enabled: true,
      knowledge: { repos: [] },
      mcp: { servers: {} },
      extensions: { agents_md: "", user_skills_dir: "" },
    }),
  });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.detail || "创建项目失败");
  toast(`项目 ${name} 已创建`, "success");
  toggleCreateProjectPanel(false);
  await loadProjects();
  if (projectConfigSelect) projectConfigSelect.value = projectId;
  await loadAdminProjectList();
}

async function saveProjectMembers() {
  const projectId = currentProjectConfigId();
  const usernames = (projectMembersEditor?.value || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  const resp = await apiFetch(`/api/admin/projects/${encodeURIComponent(projectId)}/members`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ usernames }),
  });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.detail || "保存成员失败");
  toast("成员已保存", "success");
  renderProjectMembers(data.members || []);
  await loadProjects();
}

function loadYamlDefaultMeta() {
  const defaults = adminProjectYamlDefaults;
  if (!defaults) {
    toast("请先选择项目并加载配置", "error");
    return;
  }
  if (projectMetaName) projectMetaName.value = defaults.name || "";
  if (projectMetaDescription) projectMetaDescription.value = defaults.description || "";
  if (projectMetaEnabled) projectMetaEnabled.checked = defaults.enabled !== false;
  toast("已载入 yaml 默认（基本信息），请修改后保存", "success");
}

function loadYamlDefaultRepos() {
  const defaults = adminProjectYamlDefaults;
  if (!defaults || !projectReposEditor) {
    toast("请先选择项目并加载配置", "error");
    return;
  }
  projectReposEditor.value = JSON.stringify(defaults.knowledge?.repos ?? [], null, 2);
  toast("已载入 yaml 默认（Repos），请修改后保存", "success");
}

function loadYamlDefaultMcp() {
  const defaults = adminProjectYamlDefaults;
  if (!defaults || !projectMcpEditor) {
    toast("请先选择项目并加载配置", "error");
    return;
  }
  projectMcpEditor.value = JSON.stringify(defaults.mcp?.servers ?? {}, null, 2);
  toast("已载入 yaml 默认（MCP），请修改后保存", "success");
}

function loadYamlDefaultAgents() {
  const defaults = adminProjectYamlDefaults;
  if (!defaults || !projectAgentsEditor) {
    toast("请先选择项目并加载配置", "error");
    return;
  }
  const content = defaults.extensions?.agents_md ?? "";
  projectAgentsEditor.value = content;
  syncAgentsMdTemplateSelect(content);
  toast("已载入 yaml 默认（agents.md），请修改后保存", "success");
}

function currentProjectConfigId() {
  return projectConfigSelect?.value || currentProjectId || "default";
}

async function patchProjectSection(path, body, label) {
  const projectId = currentProjectConfigId();
  const resp = await apiFetch(`/api/admin/projects/${encodeURIComponent(projectId)}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.detail || `${label}保存失败`);
  toast(`${label}已保存到 Redis`, "success");
  await loadProjects();
  await loadHealth();
  await loadAdminProjectConfig(projectId);
}

async function saveProjectMeta() {
  await patchProjectSection(
    "",
    {
      name: projectMetaName?.value?.trim() || undefined,
      description: projectMetaDescription?.value?.trim() ?? "",
      enabled: projectMetaEnabled?.checked ?? true,
    },
    "基本信息",
  );
}

async function saveProjectRepos() {
  let repos;
  try {
    repos = JSON.parse(projectReposEditor?.value || "[]");
  } catch {
    toast("Repos JSON 格式无效", "error");
    return;
  }
  if (!Array.isArray(repos)) {
    toast("Repos 必须是数组", "error");
    return;
  }
  await patchProjectSection("/knowledge", { repos }, "知识库");
}

async function saveProjectMcp() {
  let servers;
  try {
    servers = JSON.parse(projectMcpEditor?.value || "{}");
  } catch {
    toast("MCP JSON 格式无效", "error");
    return;
  }
  if (typeof servers !== "object" || servers === null || Array.isArray(servers)) {
    toast("MCP servers 必须是对象", "error");
    return;
  }
  await patchProjectSection(
    "/mcp",
    { servers },
    "MCP",
  );
}

async function saveProjectAgentsMd() {
  await patchProjectSection(
    "/extensions",
    {
      agents_md: projectAgentsEditor?.value ?? "",
    },
    "agents.md",
  );
}

function openDashboard() {
  if (!isAdmin) return;
  adminViewMode = "token";
  hideAdminPanels();
  adminDashboard.classList.remove("hidden");
  enterAdminChrome("Token 消耗", "管理员 · Token");
  updateAdminNavActive();
  loadDashboard().catch((err) => toast(err.message, "error"));
  dashboardPollTimer = window.setInterval(() => {
    loadDashboard().catch(() => {});
  }, 30000);
}

function closeAdminView({ restoreChat = true } = {}) {
  adminViewMode = null;
  hideAdminPanels();
  messagesEl.classList.remove("hidden");
  if (composerZone) composerZone.classList.remove("hidden");
  updateAdminNavActive();
  if (!restoreChat) return;
  if (currentChatId) {
    openChat(currentChatId).catch(() => clearChatPanel());
  } else {
    clearChatPanel();
  }
}

async function loadHealth() {
  try {
    const resp = await fetch("/api/health");
    if (!resp.ok) return;
    const data = await resp.json();
    modelLabelEl.textContent = data.model_label || data.model || "—";
    storageLabelEl.textContent = data.storage_backend || "—";
    const reposResp = await apiFetch(projectQuery("/api/knowledge/repos"));
    if (reposResp.ok) {
      const reposData = await reposResp.json();
      knowledgeLabelEl.textContent = Array.isArray(reposData.repos) && reposData.repos.length
        ? reposData.repos.map((r) => r.id).join(", ")
        : "未配置";
    }
  } catch { /* 忽略 */ }
}

/* --------------------------------------------------------------------------
 * 侧栏与菜单交互
 * ------------------------------------------------------------------------ */

function toggleMenu(btn, menu) {
  menu.classList.toggle("hidden");
  btn.setAttribute("aria-expanded", String(!menu.classList.contains("hidden")));
}

function closeAllMenus() {
  settingsMenu.classList.add("hidden");
  userMenu.classList.add("hidden");
}

document.addEventListener("click", (e) => {
  if (!settingsMenu.contains(e.target) && e.target !== settingsBtn && !settingsBtn.contains(e.target)) {
    settingsMenu.classList.add("hidden");
  }
  if (!userMenu.contains(e.target) && e.target !== userChipBtn && !userChipBtn.contains(e.target)) {
    userMenu.classList.add("hidden");
  }
});

settingsBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  userMenu.classList.add("hidden");
  toggleMenu(settingsBtn, settingsMenu);
});

userChipBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  settingsMenu.classList.add("hidden");
  toggleMenu(userChipBtn, userMenu);
});

function closeSidebarMobile() {
  sidebar.classList.remove("open");
  scrim.classList.add("hidden");
}

menuToggle.addEventListener("click", () => {
  sidebar.classList.add("open");
  scrim.classList.remove("hidden");
});

scrim.addEventListener("click", closeSidebarMobile);

searchInput.addEventListener("input", renderChatList);

if (adminBoardBtn) {
  adminBoardBtn.addEventListener("click", openDashboard);
}
if (projectSelectEl) {
  projectSelectEl.addEventListener("change", async () => {
    try {
      await switchProject(projectSelectEl.value);
    } catch (err) {
      toast(err.message, "error");
    }
  });
}
if (adminProjectsBtn) {
  adminProjectsBtn.addEventListener("click", () => {
    openProjectAdmin();
  });
}
if (createProjectBtn) {
  createProjectBtn.addEventListener("click", () => toggleCreateProjectPanel(true));
}
if (cancelCreateProjectBtn) {
  cancelCreateProjectBtn.addEventListener("click", () => toggleCreateProjectPanel(false));
}
if (submitCreateProjectBtn) {
  submitCreateProjectBtn.addEventListener("click", () => {
    createProject().catch((err) => toast(err.message, "error"));
  });
}
if (saveProjectMembersBtn) {
  saveProjectMembersBtn.addEventListener("click", () => {
    saveProjectMembers().catch((err) => toast(err.message, "error"));
  });
}
if (projectConfigSelect) {
  projectConfigSelect.addEventListener("change", () => {
    loadAdminProjectConfig(projectConfigSelect.value).catch((err) => toast(err.message, "error"));
  });
}
if (loadProjectMetaDefaultBtn) {
  loadProjectMetaDefaultBtn.addEventListener("click", loadYamlDefaultMeta);
}
if (loadProjectReposDefaultBtn) {
  loadProjectReposDefaultBtn.addEventListener("click", loadYamlDefaultRepos);
}
if (loadProjectMcpDefaultBtn) {
  loadProjectMcpDefaultBtn.addEventListener("click", loadYamlDefaultMcp);
}
if (loadProjectAgentsDefaultBtn) {
  loadProjectAgentsDefaultBtn.addEventListener("click", loadYamlDefaultAgents);
}
if (saveProjectMetaBtn) {
  saveProjectMetaBtn.addEventListener("click", () => {
    saveProjectMeta().catch((err) => toast(err.message, "error"));
  });
}
if (saveProjectReposBtn) {
  saveProjectReposBtn.addEventListener("click", () => {
    saveProjectRepos().catch((err) => toast(err.message, "error"));
  });
}
if (saveProjectMcpBtn) {
  saveProjectMcpBtn.addEventListener("click", () => {
    saveProjectMcp().catch((err) => toast(err.message, "error"));
  });
}
if (saveProjectAgentsBtn) {
  saveProjectAgentsBtn.addEventListener("click", () => {
    saveProjectAgentsMd().catch((err) => toast(err.message, "error"));
  });
}
if (projectAgentsTemplate) {
  projectAgentsTemplate.addEventListener("change", () => {
    applyAgentsMdTemplate(projectAgentsTemplate.value);
  });
}
if (projectAgentsEditor && projectAgentsTemplate) {
  projectAgentsEditor.addEventListener("input", () => {
    const selected = projectAgentsTemplate.value;
    if (selected === AGENTS_MD_CUSTOM_TEMPLATE_ID) return;
    const templateContent = agentsMdTemplateContent(selected);
    if ((projectAgentsEditor.value || "").trim() !== (templateContent || "").trim()) {
      projectAgentsTemplate.value = AGENTS_MD_CUSTOM_TEMPLATE_ID;
    }
  });
}
if (reloadProjectConfigBtn) {
  reloadProjectConfigBtn.addEventListener("click", () => {
    loadAdminProjectConfig(projectConfigSelect?.value || currentProjectId).catch((err) =>
      toast(err.message, "error"),
    );
  });
}
if (closeDashboardBtn) {
  closeDashboardBtn.addEventListener("click", () => closeAdminView());
}
if (closeProjectAdminBtn) {
  closeProjectAdminBtn.addEventListener("click", () => closeAdminView());
}
if (refreshDashboardBtn) {
  refreshDashboardBtn.addEventListener("click", () => {
    loadDashboard().then(() => toast("已刷新", "success")).catch((err) => toast(err.message, "error"));
  });
}

/* --------------------------------------------------------------------------
 * 侧栏与菜单动作
 * ------------------------------------------------------------------------ */

newChatBtn.addEventListener("click", async () => {
  try {
    await createChat();
  } catch (err) {
    toast(err.message, "error");
  }
});

logoutBtn.addEventListener("click", async () => {
  try {
    await apiFetch("/api/auth/logout", { method: "POST" });
  } catch { /* 忽略 */ }
  localStorage.removeItem(TOKEN_KEY);
  window.location.replace("/");
});

syncKnowledgeBtn.addEventListener("click", async () => {
  settingsMenu.classList.add("hidden");
  setStatus("同步中…", "busy");
  try {
    const resp = await apiFetch(projectQuery("/api/knowledge/sync"), { method: "POST" });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || "同步失败");
    knowledgeLabelEl.textContent = (data.synced || []).map((i) => i.repo_id).join(", ") || "已同步";
    setStatus("就绪");
    toast("知识库同步完成", "success");
  } catch (err) {
    setStatus("就绪", "error");
    toast(`同步失败: ${err.message}`, "error");
  }
});

reloadSkillsBtn.addEventListener("click", async () => {
  settingsMenu.classList.add("hidden");
  setStatus("重载中…", "busy");
  try {
    const resp = await apiFetch(projectQuery("/api/skills/reload"), { method: "POST" });
    if (!resp.ok) {
      const data = await resp.json();
      throw new Error(data.detail || "重载失败");
    }
    const data = await resp.json();
    setStatus("就绪");
    toast(`已重载 ${data.published?.length || 0} 个 Skill`, "success");
  } catch (err) {
    setStatus("就绪", "error");
    toast(`重载失败: ${err.message}`, "error");
  }
});

if (recordModeBtn) {
  recordModeBtn.addEventListener("click", () => {
    recordMode = !recordMode;
    localStorage.setItem(RECORD_MODE_KEY, recordMode ? "1" : "0");
    syncRecordModeUi();
    toast(recordMode ? "录屏模式已开启（Thinking 保持展开）" : "录屏模式已关闭", "info");
  });
}

ticketTemplateBtn.addEventListener("click", () => {
  settingsMenu.classList.add("hidden");
  if (!currentChatId) {
    toast("请先选择或新建对话", "info");
    return;
  }
  promptEl.value =
    "工单标题：服务异常\n\n现象：接口返回 500\n\n" +
    "请只读分析 workspace 中关联仓库的代码与日志，给出根因分析和修复建议。";
  autoResizePrompt();
  promptEl.focus();
});

/* --------------------------------------------------------------------------
 * 输入框
 * ------------------------------------------------------------------------ */

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = promptEl.value;
  promptEl.value = "";
  autoResizePrompt();
  sendMessage(text);
});

promptEl.addEventListener("input", autoResizePrompt);

promptEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && e.shiftKey) {
    e.preventDefault();
    chatForm.requestSubmit();
  }
});

stopBtn.addEventListener("click", async () => {
  userStoppedRun = true;
  if (chatAbortController) chatAbortController.abort();
  if (currentChatId || agentConversationId) {
    try {
      await apiFetch(projectQuery("/api/agent/cancel"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversation_id: agentConversationId,
          chat_id: currentChatId,
        }),
      });
    } catch {
      /* 忽略 cancel 失败 */
    }
  }
});

document.querySelectorAll(".hint-card").forEach((btn) => {
  btn.addEventListener("click", async () => {
    if (!currentChatId) {
      try {
        await createChat();
      } catch (err) {
        toast(err.message, "error");
        return;
      }
    }
    promptEl.value = btn.dataset.hint || "";
    autoResizePrompt();
    promptEl.focus();
  });
});

/* 启动 */
(async function bootstrap() {
  try {
    await loadMe();
    await loadProjects();
    await loadHealth();
    await refreshChats();
    clearChatPanel();
  } catch {
    localStorage.removeItem(TOKEN_KEY);
    window.location.replace("/");
  }
})();
