import {
  App,
  apiFetch,
  escapeHtml,
  toast,
  projectQuery,
  hideAdminPanels,
  enterAdminChrome,
  updateAdminNavActive,
} from "./app-shared.js";

/** agents.md 默认模板：选择后填入下方编辑框，用户可再改（与 deepticket/config/agents_defaults.py 保持一致） */
const AGENTS_MD_TEMPLATES = [
  {
    id: "",
    label: "不注入（空）",
    content: "",
  },
  {
    id: "standard",
    label: "DeepTicket 标准（推荐）",
    content: `你是 DeepTicket 项目助手，帮助同事排查故障、走读代码、分析业务指标与工单分流。

基本原则：
- 以 workspace 内的代码、日志、配置与文档为依据，引用具体路径与行号
- 先复述问题与影响面，再给出结论；不确定处明确标注「待验证」
- 默认只读：不修改代码、不执行写盘或对外发网的命令
- 不臆造配置、指标、日志或代码；没有证据时说明缺什么信息

回复结构（可按场景裁剪）：
1. 摘要 — 现象与影响
2. 分析 — 根因假设与证据
3. 建议 — 排查步骤或可执行动作

可用能力：
- 检索已同步的 Git 知识库与工作区文件
- 调用已挂载的 MCP 与 Skill（如 log-query、config-query）
- 需要权限或环境时，说明 blocker 而非强行猜测`,
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

/** @type {{ onClose?: () => void, loadProjects?: () => Promise<void>, loadHealth?: () => Promise<void>, currentProjectIdRef?: { current: string } } | null} */
let wireDeps = null;

function dom() {
  return {
    adminProjectPanel: document.getElementById("adminProjectPanel"),
    adminProjectsBtn: document.getElementById("adminProjectsBtn"),
    messagesEl: document.getElementById("messages"),
    composerZone: document.querySelector(".composer-zone"),
    chatTitleEl: document.getElementById("chatTitle"),
    conversationIdEl: document.getElementById("conversationId"),
    projectConfigSelect: document.getElementById("projectConfigSelect"),
    projectCreatePanel: document.getElementById("projectCreatePanel"),
    createProjectBtn: document.getElementById("createProjectBtn"),
    cancelCreateProjectBtn: document.getElementById("cancelCreateProjectBtn"),
    submitCreateProjectBtn: document.getElementById("submitCreateProjectBtn"),
    newProjectId: document.getElementById("newProjectId"),
    newProjectName: document.getElementById("newProjectName"),
    newProjectDescription: document.getElementById("newProjectDescription"),
    projectMembersTags: document.getElementById("projectMembersTags"),
    projectMembersEditor: document.getElementById("projectMembersEditor"),
    saveProjectMembersBtn: document.getElementById("saveProjectMembersBtn"),
    projectConfigHint: document.getElementById("projectConfigHint"),
    projectMetaName: document.getElementById("projectMetaName"),
    projectMetaDescription: document.getElementById("projectMetaDescription"),
    projectMetaEnabled: document.getElementById("projectMetaEnabled"),
    projectReposEditor: document.getElementById("projectReposEditor"),
    projectMcpEditor: document.getElementById("projectMcpEditor"),
    projectAgentsTemplate: document.getElementById("projectAgentsTemplate"),
    projectAgentsEditor: document.getElementById("projectAgentsEditor"),
    saveProjectMetaBtn: document.getElementById("saveProjectMetaBtn"),
    loadProjectMetaDefaultBtn: document.getElementById("loadProjectMetaDefaultBtn"),
    saveProjectReposBtn: document.getElementById("saveProjectReposBtn"),
    loadProjectReposDefaultBtn: document.getElementById("loadProjectReposDefaultBtn"),
    saveProjectMcpBtn: document.getElementById("saveProjectMcpBtn"),
    loadProjectMcpDefaultBtn: document.getElementById("loadProjectMcpDefaultBtn"),
    saveProjectAgentsBtn: document.getElementById("saveProjectAgentsBtn"),
    loadProjectAgentsDefaultBtn: document.getElementById("loadProjectAgentsDefaultBtn"),
    reloadProjectConfigBtn: document.getElementById("reloadProjectConfigBtn"),
    closeProjectAdminBtn: document.getElementById("closeProjectAdminBtn"),
    closeSidebarMobile: () => {
      document.getElementById("sidebar")?.classList.remove("open");
      document.getElementById("scrim")?.classList.add("hidden");
    },
  };
}

function currentProjectId() {
  return wireDeps?.currentProjectIdRef?.current ?? App.currentProjectId;
}

export function openProjectAdmin() {
  if (!App.isAdmin) return;
  const d = dom();
  App.adminViewMode = "projects";
  hideAdminPanels(d);
  d.adminProjectPanel?.classList.remove("hidden");
  toggleCreateProjectPanel(false);
  enterAdminChrome(d, "项目配置", "管理员 · 项目");
  updateAdminNavActive(d);
  ensureAgentsMdTemplateOptions();
  loadAdminProjectList().catch((err) => toast(err.message, "error"));
}

function ensureAgentsMdTemplateOptions() {
  const d = dom();
  if (!d.projectAgentsTemplate || d.projectAgentsTemplate.dataset.ready === "1") return;
  const options = AGENTS_MD_TEMPLATES.map(
    (item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.label)}</option>`,
  );
  options.push(
    `<option value="${AGENTS_MD_CUSTOM_TEMPLATE_ID}">自定义（保留当前内容）</option>`,
  );
  d.projectAgentsTemplate.innerHTML = options.join("");
  d.projectAgentsTemplate.dataset.ready = "1";
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
  const d = dom();
  if (!d.projectAgentsTemplate) return;
  d.projectAgentsTemplate.value = matchAgentsMdTemplateId(content);
}

function applyAgentsMdTemplate(templateId) {
  const d = dom();
  if (templateId === AGENTS_MD_CUSTOM_TEMPLATE_ID) return;
  const content = agentsMdTemplateContent(templateId);
  if (content !== null && d.projectAgentsEditor) {
    d.projectAgentsEditor.value = content;
  }
}

async function loadAdminProjectList() {
  const d = dom();
  const resp = await apiFetch("/api/admin/projects");
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.detail || "加载项目配置失败");
  const projects = data.projects || [];
  if (d.projectConfigSelect) {
    d.projectConfigSelect.innerHTML = projects
      .map(
        (item) =>
          `<option value="${escapeHtml(item.id)}">${escapeHtml(item.name)} (${escapeHtml(item.id)})</option>`,
      )
      .join("");
  }
  ensureAgentsMdTemplateOptions();
  const selected = d.projectConfigSelect?.value || currentProjectId() || "default";
  await loadAdminProjectConfig(selected);
}

async function loadAdminProjectConfig(projectId) {
  const d = dom();
  const resp = await apiFetch(`/api/admin/projects/${encodeURIComponent(projectId)}`);
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.detail || "读取项目配置失败");
  const project = data.project || {};
  const defaults = data.defaults || {};
  App.adminProjectYamlDefaults = defaults;
  if (d.projectConfigHint) {
    const source = data.in_redis ? "Redis + yaml 兜底" : "仅 yaml 兜底（尚未写入 Redis）";
    d.projectConfigHint.textContent = `当前生效：${source}。编辑框显示当前生效值；点「载入 yaml 默认」可单独填入 deepticket.yaml 兜底，改完再保存。`;
  }
  if (d.projectMetaName) d.projectMetaName.value = project.name || "";
  if (d.projectMetaDescription) d.projectMetaDescription.value = project.description || "";
  if (d.projectMetaEnabled) d.projectMetaEnabled.checked = project.enabled !== false;
  if (d.projectReposEditor) {
    d.projectReposEditor.value = JSON.stringify(project.knowledge?.repos ?? [], null, 2);
  }
  if (d.projectMcpEditor) {
    d.projectMcpEditor.value = JSON.stringify(project.mcp?.servers ?? {}, null, 2);
  }
  if (d.projectAgentsEditor) {
    const savedAgentsMd = project.extensions?.agents_md ?? "";
    d.projectAgentsEditor.value = savedAgentsMd;
    syncAgentsMdTemplateSelect(savedAgentsMd);
  }
  renderProjectMembers(data.members || []);
}

function renderProjectMembers(members) {
  const d = dom();
  if (!d.projectMembersTags || !d.projectMembersEditor) return;
  const list = Array.isArray(members) ? members : [];
  if (!list.length) {
    d.projectMembersTags.classList.add("empty");
    d.projectMembersTags.innerHTML = "";
  } else {
    d.projectMembersTags.classList.remove("empty");
    d.projectMembersTags.innerHTML = list
      .map((item) => `<span class="project-member-tag">${escapeHtml(item.username || item.uid)}</span>`)
      .join("");
  }
  d.projectMembersEditor.value = list.map((item) => item.username).filter(Boolean).join("\n");
}

function normalizeProjectId(raw) {
  return (raw || "").trim().toLowerCase();
}

function isValidProjectId(projectId) {
  return /^[a-z0-9][a-z0-9_-]{0,63}$/.test(projectId);
}

function toggleCreateProjectPanel(show) {
  const d = dom();
  if (!d.projectCreatePanel) return;
  d.projectCreatePanel.classList.toggle("hidden", !show);
  if (show) {
    if (d.newProjectId) d.newProjectId.value = "";
    if (d.newProjectName) d.newProjectName.value = "";
    if (d.newProjectDescription) d.newProjectDescription.value = "";
    d.newProjectId?.focus();
  }
}

async function createProject() {
  const d = dom();
  const projectId = normalizeProjectId(d.newProjectId?.value);
  const name = (d.newProjectName?.value || "").trim();
  const description = (d.newProjectDescription?.value || "").trim();
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
  await wireDeps?.loadProjects?.();
  if (d.projectConfigSelect) d.projectConfigSelect.value = projectId;
  await loadAdminProjectList();
}

async function saveProjectMembers() {
  const d = dom();
  const projectId = currentProjectConfigId();
  const usernames = (d.projectMembersEditor?.value || "")
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
  await wireDeps?.loadProjects?.();
}

function loadYamlDefaultMeta() {
  const d = dom();
  const defaults = App.adminProjectYamlDefaults;
  if (!defaults) {
    toast("请先选择项目并加载配置", "error");
    return;
  }
  if (d.projectMetaName) d.projectMetaName.value = defaults.name || "";
  if (d.projectMetaDescription) d.projectMetaDescription.value = defaults.description || "";
  if (d.projectMetaEnabled) d.projectMetaEnabled.checked = defaults.enabled !== false;
  toast("已载入 yaml 默认（基本信息），请修改后保存", "success");
}

function loadYamlDefaultRepos() {
  const d = dom();
  const defaults = App.adminProjectYamlDefaults;
  if (!defaults || !d.projectReposEditor) {
    toast("请先选择项目并加载配置", "error");
    return;
  }
  d.projectReposEditor.value = JSON.stringify(defaults.knowledge?.repos ?? [], null, 2);
  toast("已载入 yaml 默认（Repos），请修改后保存", "success");
}

function loadYamlDefaultMcp() {
  const d = dom();
  const defaults = App.adminProjectYamlDefaults;
  if (!defaults || !d.projectMcpEditor) {
    toast("请先选择项目并加载配置", "error");
    return;
  }
  d.projectMcpEditor.value = JSON.stringify(defaults.mcp?.servers ?? {}, null, 2);
  toast("已载入 yaml 默认（MCP），请修改后保存", "success");
}

function loadYamlDefaultAgents() {
  const d = dom();
  const defaults = App.adminProjectYamlDefaults;
  if (!defaults || !d.projectAgentsEditor) {
    toast("请先选择项目并加载配置", "error");
    return;
  }
  const content = defaults.extensions?.agents_md ?? "";
  d.projectAgentsEditor.value = content;
  syncAgentsMdTemplateSelect(content);
  toast("已载入 yaml 默认（agents.md），请修改后保存", "success");
}

function currentProjectConfigId() {
  const d = dom();
  return d.projectConfigSelect?.value || currentProjectId() || "default";
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
  await wireDeps?.loadProjects?.();
  await wireDeps?.loadHealth?.();
  await loadAdminProjectConfig(projectId);
}

async function saveProjectMeta() {
  const d = dom();
  await patchProjectSection(
    "",
    {
      name: d.projectMetaName?.value?.trim() || undefined,
      description: d.projectMetaDescription?.value?.trim() ?? "",
      enabled: d.projectMetaEnabled?.checked ?? true,
    },
    "基本信息",
  );
}

async function saveProjectRepos() {
  const d = dom();
  let repos;
  try {
    repos = JSON.parse(d.projectReposEditor?.value || "[]");
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
  const d = dom();
  let servers;
  try {
    servers = JSON.parse(d.projectMcpEditor?.value || "{}");
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
  const d = dom();
  await patchProjectSection(
    "/extensions",
    {
      agents_md: d.projectAgentsEditor?.value ?? "",
    },
    "agents.md",
  );
}

export function wireAdminProjects({ onClose, loadProjects, loadHealth, currentProjectIdRef }) {
  wireDeps = { onClose, loadProjects, loadHealth, currentProjectIdRef };

  document.getElementById("adminProjectsBtn")?.addEventListener("click", () => openProjectAdmin());
  document.getElementById("createProjectBtn")?.addEventListener("click", () => toggleCreateProjectPanel(true));
  document.getElementById("cancelCreateProjectBtn")?.addEventListener("click", () => toggleCreateProjectPanel(false));
  document.getElementById("submitCreateProjectBtn")?.addEventListener("click", () => {
    createProject().catch((err) => toast(err.message, "error"));
  });
  document.getElementById("saveProjectMembersBtn")?.addEventListener("click", () => {
    saveProjectMembers().catch((err) => toast(err.message, "error"));
  });
  document.getElementById("projectConfigSelect")?.addEventListener("change", (event) => {
    loadAdminProjectConfig(event.target.value).catch((err) => toast(err.message, "error"));
  });
  document.getElementById("loadProjectMetaDefaultBtn")?.addEventListener("click", loadYamlDefaultMeta);
  document.getElementById("loadProjectReposDefaultBtn")?.addEventListener("click", loadYamlDefaultRepos);
  document.getElementById("loadProjectMcpDefaultBtn")?.addEventListener("click", loadYamlDefaultMcp);
  document.getElementById("loadProjectAgentsDefaultBtn")?.addEventListener("click", loadYamlDefaultAgents);
  document.getElementById("saveProjectMetaBtn")?.addEventListener("click", () => {
    saveProjectMeta().catch((err) => toast(err.message, "error"));
  });
  document.getElementById("saveProjectReposBtn")?.addEventListener("click", () => {
    saveProjectRepos().catch((err) => toast(err.message, "error"));
  });
  document.getElementById("saveProjectMcpBtn")?.addEventListener("click", () => {
    saveProjectMcp().catch((err) => toast(err.message, "error"));
  });
  document.getElementById("saveProjectAgentsBtn")?.addEventListener("click", () => {
    saveProjectAgentsMd().catch((err) => toast(err.message, "error"));
  });
  document.getElementById("projectAgentsTemplate")?.addEventListener("change", (event) => {
    applyAgentsMdTemplate(event.target.value);
  });
  const projectAgentsEditor = document.getElementById("projectAgentsEditor");
  const projectAgentsTemplate = document.getElementById("projectAgentsTemplate");
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
  document.getElementById("reloadProjectConfigBtn")?.addEventListener("click", () => {
    const projectConfigSelect = document.getElementById("projectConfigSelect");
    loadAdminProjectConfig(projectConfigSelect?.value || currentProjectId()).catch((err) =>
      toast(err.message, "error"),
    );
  });
  document.getElementById("closeProjectAdminBtn")?.addEventListener("click", () => onClose?.());
}
