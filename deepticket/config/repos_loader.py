from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from deepticket.config.schema import GitRepoConfig


def _parse_repo_list(raw: Any) -> list[GitRepoConfig]:
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict):
        items = raw.get("repos", [])
    else:
        raise ValueError("Git 仓库配置必须是 list 或 {\"repos\": [...]} 格式")

    if not isinstance(items, list):
        raise ValueError("repos 字段必须是数组")

    repos: list[GitRepoConfig] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"repos[{index}] 必须是对象")
        repos.append(GitRepoConfig.model_validate(item))
    return repos


def load_git_repos_from_json(raw: str | Any) -> list[GitRepoConfig]:
    if isinstance(raw, str):
        if not raw.strip():
            return []
        data = json.loads(raw)
    else:
        data = raw
    return _parse_repo_list(data)


def load_git_repos_from_file(path: str | Path) -> list[GitRepoConfig]:
    config_path = Path(path)
    if not config_path.is_file():
        return []
    return load_git_repos_from_json(config_path.read_text(encoding="utf-8"))


def load_git_repos_from_env(*, config_path: str | Path) -> list[GitRepoConfig]:
    """加载 Git 仓库列表：GIT_REPOS_JSON > repos.json > 空。"""
    inline = os.environ.get("GIT_REPOS_JSON", "").strip()
    if inline:
        return load_git_repos_from_json(inline)
    return load_git_repos_from_file(config_path)
