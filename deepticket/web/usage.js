import {
  App,
  TOKEN_KEY,
  apiFetch,
  escapeHtml,
  formatModel,
  formatTime,
  formatToken,
  toast,
} from "./app-shared.js";

async function ensureAuth() {
  if (!App.authToken) {
    window.location.replace("/");
    return false;
  }
  const resp = await apiFetch("/api/auth/me");
  const data = await resp.json();
  if (!resp.ok) {
    window.location.replace("/");
    return false;
  }
  App.isAdmin = Boolean(data.is_admin);
  document.getElementById("usageUserLabel").textContent = `${data.username} · 跨项目累计（仅本人）`;
  return true;
}

function renderSummary(data) {
  const summary = data.summary || {};
  document.getElementById("usageSummary").innerHTML = `
    <article class="metric-card"><span class="metric-label">Prompt</span><strong>${formatToken(summary.prompt_tokens)}</strong><span class="metric-sub">累计输入</span></article>
    <article class="metric-card"><span class="metric-label">Completion</span><strong>${formatToken(summary.completion_tokens)}</strong><span class="metric-sub">累计输出</span></article>
    <article class="metric-card"><span class="metric-label">Reasoning</span><strong>${formatToken(summary.reasoning_tokens)}</strong><span class="metric-sub">推理 token</span></article>
    <article class="metric-card"><span class="metric-label">Total</span><strong>${formatToken(summary.total_tokens)}</strong><span class="metric-sub">${summary.conversation_count || 0} 个会话</span></article>
  `;
}

function renderConversations(conversations) {
  const el = document.getElementById("usageConversations");
  el.innerHTML = conversations.length
    ? `<table class="dashboard-table"><thead><tr><th>会话</th><th>项目</th><th>模型</th><th>Prompt</th><th>Completion</th><th>Reasoning</th><th>Total</th><th>更新时间</th></tr></thead><tbody>${conversations
        .map(
          (item) =>
            `<tr><td><span class="token-chat-title">${escapeHtml(item.chat_title || "新会话")}</span><code>${escapeHtml(item.chat_id || "")}</code></td><td><code>${escapeHtml(item.project_id || "default")}</code></td><td><span class="token-model-label">${formatModel(item)}</span></td><td>${formatToken(item.prompt_tokens)}</td><td>${formatToken(item.completion_tokens)}</td><td>${formatToken(item.reasoning_tokens)}</td><td><strong>${formatToken(item.total_tokens)}</strong></td><td>${formatTime(item.updated_at)}</td></tr>`,
        )
        .join("")}</tbody></table>`
    : '<div class="dashboard-empty">暂无 token 记录，在工作台发起 Agent 对话后会自动采集</div>';
}

function renderRuns(runs) {
  const el = document.getElementById("usageRuns");
  el.innerHTML = runs.length
    ? `<table class="dashboard-table"><thead><tr><th>时间</th><th>会话</th><th>模型</th><th>本次 Prompt</th><th>本次 Completion</th><th>本次 Reasoning</th><th>本次 Total</th></tr></thead><tbody>${runs
        .map(
          (item) =>
            `<tr><td>${formatTime(item.recorded_at)}</td><td><span class="token-chat-title">${escapeHtml(item.chat_title || "新会话")}</span><code>${escapeHtml(item.chat_id || "")}</code></td><td><span class="token-model-label">${formatModel(item)}</span></td><td>${formatToken(item.prompt_tokens)}</td><td>${formatToken(item.completion_tokens)}</td><td>${formatToken(item.reasoning_tokens)}</td><td><strong>${formatToken(item.total_tokens)}</strong></td></tr>`,
        )
        .join("")}</tbody></table>`
    : '<div class="dashboard-empty">暂无单次运行记录</div>';
}

async function loadUsage() {
  const [summaryResp, runsResp] = await Promise.all([
    apiFetch("/api/usage/summary"),
    apiFetch("/api/usage/runs?limit=20"),
  ]);
  const summaryData = await summaryResp.json();
  const runsData = await runsResp.json();
  if (!summaryResp.ok) throw new Error(summaryData.detail || "加载用量摘要失败");
  if (!runsResp.ok) throw new Error(runsData.detail || "加载运行记录失败");
  renderSummary(summaryData);
  renderConversations(summaryData.conversations || []);
  renderRuns(runsData.runs || []);
}

document.getElementById("refreshUsageBtn")?.addEventListener("click", () => {
  loadUsage()
    .then(() => toast("已刷新", "success"))
    .catch((err) => toast(err.message, "error"));
});

ensureAuth()
  .then((ok) => {
    if (!ok) return;
    loadUsage().catch((err) => toast(err.message, "error"));
  })
  .catch(() => {
    localStorage.removeItem(TOKEN_KEY);
    window.location.replace("/");
  });
