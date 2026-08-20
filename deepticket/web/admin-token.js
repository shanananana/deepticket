import {
  App,
  apiFetch,
  escapeHtml,
  enterAdminChrome,
  formatModel,
  formatTime,
  formatToken,
  hideAdminPanels,
  toast,
  updateAdminNavActive,
} from "./app-shared.js";

function dom() {
  return {
    adminDashboard: document.getElementById("adminDashboard"),
    adminBoardBtn: document.getElementById("adminBoardBtn"),
    messagesEl: document.getElementById("messages"),
    composerZone: document.querySelector(".composer-zone"),
    chatTitleEl: document.getElementById("chatTitle"),
    conversationIdEl: document.getElementById("conversationId"),
    tokenSummary: document.getElementById("tokenSummary"),
    tokenConversations: document.getElementById("tokenConversations"),
    tokenRuns: document.getElementById("tokenRuns"),
    closeSidebarMobile: () => {
      document.getElementById("sidebar")?.classList.remove("open");
      document.getElementById("scrim")?.classList.add("hidden");
    },
  };
}

function renderTokenUsage(data) {
  const d = dom();
  const summary = data.summary || {};
  d.tokenSummary.innerHTML = `
    <article class="metric-card"><span class="metric-label">Prompt</span><strong>${formatToken(summary.prompt_tokens)}</strong><span class="metric-sub">累计输入</span></article>
    <article class="metric-card"><span class="metric-label">Completion</span><strong>${formatToken(summary.completion_tokens)}</strong><span class="metric-sub">累计输出</span></article>
    <article class="metric-card"><span class="metric-label">Reasoning</span><strong>${formatToken(summary.reasoning_tokens)}</strong><span class="metric-sub">推理 token</span></article>
    <article class="metric-card"><span class="metric-label">Total</span><strong>${formatToken(summary.total_tokens)}</strong><span class="metric-sub">${summary.conversation_count || 0} 个对话</span></article>
  `;
  const conversations = data.conversations || [];
  d.tokenConversations.innerHTML = conversations.length
    ? `<table class="dashboard-table"><thead><tr><th>用户</th><th>对话</th><th>模型</th><th>Prompt</th><th>Completion</th><th>Reasoning</th><th>Total</th><th>更新时间</th></tr></thead><tbody>${conversations.map((item) => `<tr><td>${escapeHtml(item.username || "—")}</td><td><span class="token-chat-title">${escapeHtml(item.chat_title || "新会话")}</span><code>${escapeHtml(item.chat_id || "")}</code></td><td><span class="token-model-label">${formatModel(item)}</span><code>${escapeHtml(item.model || "")}</code></td><td>${formatToken(item.prompt_tokens)}</td><td>${formatToken(item.completion_tokens)}</td><td>${formatToken(item.reasoning_tokens)}</td><td><strong>${formatToken(item.total_tokens)}</strong></td><td>${formatTime(item.updated_at)}</td></tr>`).join("")}</tbody></table>`
    : '<div class="dashboard-empty">暂无 token 记录，用户发起 Agent 对话后会自动采集</div>';
  const runs = data.runs || [];
  d.tokenRuns.innerHTML = runs.length
    ? `<table class="dashboard-table"><thead><tr><th>时间</th><th>用户</th><th>对话</th><th>模型</th><th>本次 Prompt</th><th>本次 Completion</th><th>本次 Reasoning</th><th>本次 Total</th></tr></thead><tbody>${runs.map((item) => `<tr><td>${formatTime(item.recorded_at)}</td><td>${escapeHtml(item.username || "—")}</td><td><span class="token-chat-title">${escapeHtml(item.chat_title || "新会话")}</span><code>${escapeHtml(item.chat_id || "")}</code></td><td><span class="token-model-label">${formatModel(item)}</span><code>${escapeHtml(item.model || "")}</code></td><td>${formatToken(item.prompt_tokens)}</td><td>${formatToken(item.completion_tokens)}</td><td>${formatToken(item.reasoning_tokens)}</td><td><strong>${formatToken(item.total_tokens)}</strong></td></tr>`).join("")}</tbody></table>`
    : '<div class="dashboard-empty">暂无单次运行记录</div>';
}

async function loadDashboard() {
  const resp = await apiFetch("/api/admin/token-usage");
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.detail || "加载 Token 消耗失败");
  renderTokenUsage(data);
}

export function openDashboard() {
  if (!App.isAdmin) return;
  const d = dom();
  App.adminViewMode = "token";
  hideAdminPanels(d);
  d.adminDashboard?.classList.remove("hidden");
  enterAdminChrome(d, "Token 消耗", "管理员 · Token");
  updateAdminNavActive(d);
  loadDashboard().catch((err) => toast(err.message, "error"));
  App.dashboardPollTimer = window.setInterval(() => {
    loadDashboard().catch(() => {});
  }, 30000);
}

export function wireAdminToken({ onRestoreChat }) {
  document.getElementById("adminBoardBtn")?.addEventListener("click", openDashboard);
  document.getElementById("closeDashboardBtn")?.addEventListener("click", () =>
    onRestoreChat?.(),
  );
  document.getElementById("refreshDashboardBtn")?.addEventListener("click", () => {
    loadDashboard().then(() => toast("已刷新", "success")).catch((err) => toast(err.message, "error"));
  });
}
