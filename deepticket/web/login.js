const TOKEN_KEY = "deepticket_token";

const tabs = document.getElementById("authTabs");
const loginTabBtn = document.getElementById("loginTabBtn");
const registerTabBtn = document.getElementById("registerTabBtn");
const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");
const authError = document.getElementById("authError");

function setAuthError(text) {
  authError.textContent = text || "";
}

function switchTab(mode) {
  const isLogin = mode === "login";
  tabs.dataset.mode = mode;
  loginTabBtn.classList.toggle("active", isLogin);
  registerTabBtn.classList.toggle("active", !isLogin);
  loginForm.classList.toggle("hidden", !isLogin);
  registerForm.classList.toggle("hidden", isLogin);
  setAuthError("");
  (isLogin ? loginForm : registerForm).querySelector("input")?.focus();
}

async function postJson(url, body) {
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  let data = {};
  try {
    data = await resp.json();
  } catch {
    // 非 JSON 响应时保持空对象，由下方统一报错
  }
  if (!resp.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : "请求失败");
  }
  return data;
}

async function login(username, password) {
  const data = await postJson("/api/auth/login", { username, password });
  localStorage.setItem(TOKEN_KEY, data.token);
  window.location.href = "/app";
}

function bindSubmit(form, handler) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    setAuthError("");
    const button = form.querySelector("button[type=submit]");
    const label = button.querySelector("span");
    const original = label ? label.textContent : "";
    button.disabled = true;
    if (label) label.textContent = "处理中…";
    try {
      await handler();
    } catch (err) {
      setAuthError(err.message);
      button.disabled = false;
      if (label) label.textContent = original;
    }
  });
}

loginTabBtn.addEventListener("click", () => switchTab("login"));
registerTabBtn.addEventListener("click", () => switchTab("register"));

bindSubmit(loginForm, () =>
  login(
    document.getElementById("loginUsername").value.trim(),
    document.getElementById("loginPassword").value
  )
);

bindSubmit(registerForm, async () => {
  const username = document.getElementById("registerUsername").value.trim();
  const password = document.getElementById("registerPassword").value;
  await postJson("/api/auth/register", { username, password });
  await login(username, password);
});

(async function redirectIfSignedIn() {
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) return;
  try {
    const resp = await fetch("/api/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (resp.ok) {
      window.location.replace("/app");
      return;
    }
  } catch {
    // 网络异常时留在登录页
  }
  localStorage.removeItem(TOKEN_KEY);
})();
