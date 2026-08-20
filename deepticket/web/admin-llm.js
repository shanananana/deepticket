import {
  App,
  apiFetch,
  enterAdminChrome,
  hideAdminPanels,
  toast,
  updateAdminNavActive,
} from "./app-shared.js";

function dom() {
  return {
    adminLlmPanel: document.getElementById("adminLlmPanel"),
    adminLlmBtn: document.getElementById("adminLlmBtn"),
    messagesEl: document.getElementById("messages"),
    composerZone: document.querySelector(".composer-zone"),
    chatTitleEl: document.getElementById("chatTitle"),
    conversationIdEl: document.getElementById("conversationId"),
    llmModelInput: document.getElementById("llmModelInput"),
    llmBaseUrlInput: document.getElementById("llmBaseUrlInput"),
    llmLabelInput: document.getElementById("llmLabelInput"),
    llmApiKeyInput: document.getElementById("llmApiKeyInput"),
    llmConfigPath: document.getElementById("llmConfigPath"),
    llmConfigStatus: document.getElementById("llmConfigStatus"),
    closeSidebarMobile: () => {
      document.getElementById("sidebar")?.classList.remove("open");
      document.getElementById("scrim")?.classList.add("hidden");
    },
  };
}

export async function loadAdminLlmConfig() {
  const d = dom();
  const resp = await apiFetch("/api/admin/llm");
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.detail || "加载 LLM 配置失败");
  if (d.llmModelInput) d.llmModelInput.value = data.model || "";
  if (d.llmBaseUrlInput) d.llmBaseUrlInput.value = data.base_url || "";
  if (d.llmLabelInput) d.llmLabelInput.value = data.label || "";
  if (d.llmApiKeyInput) d.llmApiKeyInput.value = "";
  if (d.llmConfigPath) d.llmConfigPath.textContent = data.config_path || "—";
  if (d.llmConfigStatus) {
    d.llmConfigStatus.textContent = data.configured
      ? `已配置（${data.api_key_hint || "密钥已保存"}）`
      : "尚未配置 API Key，保存后即可使用 Agent。";
  }
  return data;
}

export async function saveLlmConfig(onHealth) {
  const d = dom();
  const apiKey = d.llmApiKeyInput?.value?.trim() || "";
  if (!apiKey) {
    toast("请填写 API Key", "error");
    return;
  }
  const body = {
    api_key: apiKey,
    model: d.llmModelInput?.value?.trim() || "openai/deepseek-v4-flash",
    base_url: d.llmBaseUrlInput?.value?.trim() || "https://api.deepseek.com/v1",
    label: d.llmLabelInput?.value?.trim() || "DeepSeek V4 Flash",
  };
  const resp = await apiFetch("/api/admin/llm", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.detail || "保存 LLM 配置失败");
  App.llmConfigured = true;
  if (d.llmApiKeyInput) d.llmApiKeyInput.value = "";
  if (d.llmConfigStatus) {
    d.llmConfigStatus.textContent = `已配置（${data.api_key_hint || "密钥已保存"}）`;
  }
  await onHealth?.();
  toast("LLM 配置已保存", "success");
}

export function openLlmAdmin() {
  if (!App.isAdmin) return;
  const d = dom();
  App.adminViewMode = "llm";
  hideAdminPanels(d);
  d.adminLlmPanel?.classList.remove("hidden");
  enterAdminChrome(d, "LLM 配置", "管理员 · LLM");
  updateAdminNavActive(d);
  loadAdminLlmConfig().catch((err) => toast(err.message, "error"));
}

export function wireAdminLlm({ onClose, onHealth }) {
  document.getElementById("adminLlmBtn")?.addEventListener("click", () => openLlmAdmin());
  document.getElementById("saveLlmConfigBtn")?.addEventListener("click", () => {
    saveLlmConfig(onHealth).catch((err) => toast(err.message, "error"));
  });
  document.getElementById("closeLlmAdminBtn")?.addEventListener("click", () => onClose?.());
}
