from __future__ import annotations

from urllib.parse import urlparse, urlunparse

from deepticket.config.schema import GitRepoConfig


def _is_gitlab_host(hostname: str) -> bool:
    host = hostname.lower()
    return host == "gitlab.com" or host.endswith(".gitlab.com") or host.startswith("gitlab.")


def build_authenticated_git_url(repo: GitRepoConfig) -> str:
    """用 key 拼出可 clone 的只读 Git 地址。

    - file:// 本地仓库：直接返回 url（无需 key）
    - GitHub 等：token 作为用户名（https://{token}@host/path）
    - GitLab（含自建 *.gitlab.com / gitlab.*）：oauth2:{token}@
    - 自建特殊格式：配置 url_template，如 https://oauth2:{key}@gitlab.corp.com/...
    """
    parsed = urlparse(repo.url)
    if parsed.scheme == "file":
        return repo.url

    key = repo.key.strip()
    if not key:
        raise ValueError(f"Git 仓库 {repo.id} 缺少 key")

    if repo.url_template:
        return repo.url_template.replace("{key}", key)

    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Git 仓库 {repo.id} 仅支持 http/https 或 file URL")

    hostname = parsed.hostname or ""
    if parsed.port:
        hostname = f"{hostname}:{parsed.port}"

    if _is_gitlab_host(parsed.hostname or ""):
        auth_netloc = f"oauth2:{key}@{hostname}"
    else:
        auth_netloc = f"{key}@{hostname}"

    return urlunparse(
        (
            parsed.scheme,
            auth_netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )


def public_repo_info(repo: GitRepoConfig) -> dict[str, str]:
    """返回不含密钥的仓库信息（供 API 展示）。"""
    return {
        "id": repo.id,
        "url": repo.url,
        "branch": repo.branch,
        "workspace_subdir": repo.workspace_subdir or repo.id,
        "url_template": repo.url_template or "",
    }
