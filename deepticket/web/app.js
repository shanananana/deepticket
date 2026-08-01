import { renderMarkdown } from "/static/markdown.js";

const TOKEN_KEY = "deepticket_token";

const ICONS = {
  edit: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4Z"/></svg>',
  trash: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>',
  copy: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>',
  check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
  chevron: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>',
};

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
const logoutBtn = $("logoutBtn");
const settingsBtn = $("settingsBtn");
const settingsMenu = $("settingsMenu");
const userChipBtn = $("userChipBtn");
const userMenu = $("userMenu");
const sidebar = $("sidebar");
const scrim = $("scrim");
const menuToggle = $("menuToggle");
const toastStack = $("toastStack");

/* 状态 */
let authToken = localStorage.getItem(TOKEN_KEY) || "";
let currentUser = null;
let currentChatId = null;
let agentConversationId = null;
let busy = false;
let chatAbortController = null;
let allChats = [];

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

function createAssistantShell(withThinking) {
  const { row, body, content } = createMessageRow("assistant");
  let thinking = null;
  if (withThinking) {
    thinking = createThinkingBlock();
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
function createThinkingBlock() {
  const root = document.createElement("div");
  root.className = "thinking active";
  root.innerHTML = `
    <button type="button" class="thinking-toggle">
      <span class="thinking-spinner"></span>
      <span class="thinking-check">✓</span>
      <span class="thinking-label">正在准备</span>
      <span class="thinking-elapsed">0s</span>
      <span class="thinking-chevron">${ICONS.chevron}</span>
    </button>
    <div class="thinking-body">
      <div class="thinking-steps"></div>
      <div class="thinking-shimmer"></div>
    </div>
  `;

  const toggle = root.querySelector(".thinking-toggle");
  const stepsEl = root.querySelector(".thinking-steps");
  const elapsedEl = root.querySelector(".thinking-elapsed");
  const labelEl = root.querySelector(".thinking-label");
  const activities = [];
  let currentActivity = "";

  toggle.addEventListener("click", () => root.classList.toggle("collapsed"));

  const renderSteps = () => {
    stepsEl.innerHTML = "";
    if (!activities.length) {
      const empty = document.createElement("div");
      empty.className = "thinking-step current";
      empty.innerHTML = `<span class="step-dot"></span><span>等待 Agent 响应…</span>`;
      stepsEl.appendChild(empty);
      return;
    }
    activities.forEach((text, idx) => {
      const step = document.createElement("div");
      step.className = "thinking-step";
      const isLast = idx === activities.length - 1;
      if (isLast) step.classList.add("current");
      else step.classList.add("done");
      step.innerHTML = `<span class="step-dot"></span><span>${escapeHtml(text)}</span>`;
      stepsEl.appendChild(step);
    });
    scrollToBottom();
  };

  const startedAt = Date.now();
  const elapsedTimer = window.setInterval(() => {
    elapsedEl.textContent = `${Math.max(1, Math.round((Date.now() - startedAt) / 1000))}s`;
  }, 250);

  renderSteps();

  return {
    root,
    addActivity(text) {
      const next = (text || "").trim();
      if (!next || next === currentActivity) return;
      currentActivity = next;
      if (activities[activities.length - 1] !== next) {
        activities.push(next);
      }
      labelEl.textContent = next;
      renderSteps();
    },
    finish(contentStarted = false) {
      window.clearInterval(elapsedTimer);
      const seconds = Math.max(1, Math.round((Date.now() - startedAt) / 1000));
      elapsedEl.textContent = `${seconds}s`;
      root.classList.remove("active");
      root.classList.add("done");
      stepsEl.querySelectorAll(".thinking-step").forEach((el) => {
        el.classList.remove("current");
        el.classList.add("done");
      });
      root.querySelector(".thinking-shimmer")?.remove();
      if (contentStarted) {
        labelEl.textContent = currentActivity
          ? `已完成 · ${seconds}s`
          : `思考用时 ${seconds}s`;
      } else {
        labelEl.textContent = currentActivity
          ? `已完成 · ${seconds}s`
          : `运行 ${seconds}s`;
      }
      window.setTimeout(() => root.classList.add("collapsed"), contentStarted ? 500 : 900);
    },
    stop() {
      window.clearInterval(elapsedTimer);
    },
  };
}

function renderHistory(messages) {
  messagesInner.querySelectorAll(".msg").forEach((el) => el.remove());
  for (const item of messages || []) {
    if (item.role === "user") {
      addUserMessage(item.content);
    } else if (item.role === "assistant") {
      const { body, content } = createAssistantShell(false);
      content.innerHTML = renderMarkdown(item.content);
      bindCodeCopy(content);
      addToolbar(body, item.content);
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
    ? allChats.filter((c) => (c.title || "").toLowerCase().includes(query))
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
        const resp = await apiFetch(`/api/chats/${chat.chat_id}`, {
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
    const resp = await apiFetch(`/api/chats/${chatId}`, { method: "DELETE" });
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
  const resp = await apiFetch("/api/chats");
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
  const resp = await apiFetch(`/api/chats/${chatId}`);
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
    body: JSON.stringify({ title: "新会话" }),
  });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.detail || "创建对话失败");
  await refreshChats();
  await openChat(data.chat.chat_id);
}

/* --------------------------------------------------------------------------
 * 发送消息（流式 + Markdown 增量渲染）
 * ------------------------------------------------------------------------ */

async function sendMessage(text) {
  const message = text.trim();
  if (!message || busy || !currentChatId) return;

  setBusy(true);
  setStatus("正在思考…", "busy");
  addUserMessage(message);

  const { body, content, thinking } = createAssistantShell(true);
  content.classList.add("placeholder");
  content.textContent = "等待 Agent 响应…";

  chatAbortController = new AbortController();
  const { signal } = chatAbortController;

  let assistantText = "";
  let contentStarted = false;
  let renderScheduled = false;

  const flushRender = () => {
    renderScheduled = false;
    content.innerHTML = renderMarkdown(assistantText);
    bindCodeCopy(content);
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
    const resp = await apiFetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        chat_id: currentChatId,
        conversation_id: agentConversationId,
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
        break;
      }
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() || "";

      for (const part of parts) {
        if (part.startsWith("event: activity")) {
          const line = part.split("\n").find((l) => l.startsWith("data: "));
          if (line) {
            try {
              const meta = JSON.parse(line.slice(6));
              if (meta.activity) thinking.addActivity(meta.activity);
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
              thinking.finish(true);
              setStatus("输出中…", "busy");
            }
            assistantText += delta;
            scheduleRender();
          }
        } catch { /* 忽略格式异常的分片 */ }
      }
    }

    if (signal.aborted) {
      thinking.stop();
      setStatus("已停止", "error");
      return;
    }

    if (renderScheduled) flushRender();
    content.classList.remove("streaming");

    if (!contentStarted) {
      thinking.finish(false);
      content.classList.remove("placeholder");
      content.textContent = "Agent 已完成运行，但未返回文本（可能仅执行了工具）。";
    } else {
      addToolbar(body, assistantText);
    }

    setStatus("就绪");
    await refreshChats();
    if (currentChatId) {
      const titleResp = await apiFetch(`/api/chats/${currentChatId}`);
      const titleData = await titleResp.json();
      if (titleResp.ok) chatTitleEl.textContent = titleData.chat.title || "新会话";
    }
  } catch (err) {
    if (err.name === "AbortError") {
      thinking.stop();
      setStatus("已停止", "error");
      return;
    }
    fail(err.message);
  } finally {
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
  userLabel.textContent = currentUser.username;
  menuUserName.textContent = currentUser.username;
  userAvatar.textContent = currentUser.username[0].toUpperCase();
}

async function loadHealth() {
  try {
    const resp = await fetch("/api/health");
    if (!resp.ok) return;
    const data = await resp.json();
    modelLabelEl.textContent = data.model_label || data.model || "—";
    knowledgeLabelEl.textContent = Array.isArray(data.knowledge_repos) && data.knowledge_repos.length
      ? data.knowledge_repos.map((r) => r.id).join(", ")
      : "未配置";
    storageLabelEl.textContent = data.storage?.backend || "—";
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
    const resp = await apiFetch("/api/knowledge/sync", { method: "POST" });
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
    const resp = await apiFetch("/api/skills/reload", { method: "POST" });
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

stopBtn.addEventListener("click", () => {
  if (chatAbortController) chatAbortController.abort();
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
    await loadHealth();
    await refreshChats();
    clearChatPanel();
  } catch {
    localStorage.removeItem(TOKEN_KEY);
    window.location.replace("/");
  }
})();
