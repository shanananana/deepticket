/**
 * 共享工作台上下文与工具（admin 模块与 app.js 共用）。
 */
export const App = {
  authToken: localStorage.getItem("deepticket_token") || "",
  currentProjectId: localStorage.getItem("deepticket_project_id") || "default",
  isAdmin: false,
  llmConfigured: true,
  adminViewMode: null,
  dashboardPollTimer: null,
  currentChatId: null,
  adminProjectYamlDefaults: null,
  availableProjects: [],
};

export const TOKEN_KEY = "deepticket_token";
export const PROJECT_KEY = "deepticket_project_id";
export const RECORD_MODE_KEY = "deepticket_record_mode";

export function projectQuery(extra = "") {
  const join = extra.includes("?") ? "&" : "?";
  return `${extra}${join}project_id=${encodeURIComponent(App.currentProjectId || "default")}`;
}

export function authHeaders(extra = {}) {
  const headers = { ...extra };
  if (App.authToken) headers.Authorization = `Bearer ${App.authToken}`;
  return headers;
}

export async function apiFetch(url, options = {}) {
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

export function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

export function toast(message, type = "info", duration = 2600) {
  const toastStack = document.getElementById("toastStack");
  if (!toastStack) return;
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.innerHTML = `<span class="toast-dot"></span><span>${escapeHtml(message)}</span>`;
  toastStack.appendChild(el);
  window.setTimeout(() => {
    el.classList.add("out");
    el.addEventListener("animationend", () => el.remove(), { once: true });
  }, duration);
}

export function formatToken(n) {
  const value = Number(n) || 0;
  return value.toLocaleString("zh-CN");
}

export function formatTime(value) {
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

export function formatModel(item) {
  return escapeHtml(item.model_label || item.model || "—");
}

export function hideAdminPanels(dom) {
  document.getElementById("adminDashboard")?.classList.add("hidden");
  document.getElementById("adminProjectPanel")?.classList.add("hidden");
  document.getElementById("adminLlmPanel")?.classList.add("hidden");
  if (App.dashboardPollTimer) {
    window.clearInterval(App.dashboardPollTimer);
    App.dashboardPollTimer = null;
  }
}

export function enterAdminChrome(dom, title, subtitle) {
  dom.messagesEl.classList.add("hidden");
  if (dom.composerZone) dom.composerZone.classList.add("hidden");
  dom.chatTitleEl.textContent = title;
  dom.conversationIdEl.textContent = subtitle;
  dom.closeSidebarMobile?.();
}

export function updateAdminNavActive(dom) {
  dom.adminBoardBtn?.classList.toggle("active", App.adminViewMode === "token");
  dom.adminProjectsBtn?.classList.toggle("active", App.adminViewMode === "projects");
  dom.adminLlmBtn?.classList.toggle("active", App.adminViewMode === "llm");
}
