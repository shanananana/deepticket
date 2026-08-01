from __future__ import annotations

import logging
import os
import shutil
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path

from deepticket.config.schema import GitRepoConfig, KnowledgeConfig
from deepticket.layers.knowledge.git_source import build_authenticated_git_url, public_repo_info

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GitSyncResult:
    repo_id: str
    cache_path: str
    workspace_path: str
    branch: str
    action: str


class KnowledgeManager:
    """知识层：从 Git 拉取只读代码到 cache，再链接到 workspace。"""

    def __init__(self, config: KnowledgeConfig) -> None:
        self.config = config
        self.cache_dir = Path(config.git_cache_dir)
        self.workspace_dir = Path(config.workspace_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def list_repos(self) -> list[dict[str, str]]:
        return [public_repo_info(repo) for repo in self.config.repos]

    def sync_all(self) -> list[GitSyncResult]:
        results: list[GitSyncResult] = []
        for repo in self.config.repos:
            results.append(self.sync_repo(repo))
        return results

    def sync_repo(self, repo: GitRepoConfig) -> GitSyncResult:
        clone_url = build_authenticated_git_url(repo)
        cache_path = self.cache_dir / repo.id
        subdir = repo.workspace_subdir or repo.id
        workspace_path = self.workspace_dir / subdir

        if cache_path.exists():
            action = self._update_repo(cache_path, repo.branch)
        else:
            action = self._clone_repo(clone_url, cache_path, repo.branch)

        self._publish_readonly_copy(cache_path, workspace_path)
        return GitSyncResult(
            repo_id=repo.id,
            cache_path=str(cache_path),
            workspace_path=str(workspace_path),
            branch=repo.branch,
            action=action,
        )

    def _clone_repo(self, clone_url: str, dest: Path, branch: str) -> str:
        if dest.exists():
            shutil.rmtree(dest)
        try:
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "--branch",
                    branch,
                    "--single-branch",
                    clone_url,
                    str(dest),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or exc.stdout or "").strip()
            raise RuntimeError(f"Git clone 失败: {stderr}") from exc
        return "cloned"

    def _update_repo(self, dest: Path, branch: str) -> str:
        try:
            subprocess.run(
                ["git", "-C", str(dest), "fetch", "--depth", "1", "origin", branch],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "-C", str(dest), "reset", "--hard", f"origin/{branch}"],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or exc.stdout or "").strip()
            raise RuntimeError(f"Git 更新失败: {stderr}") from exc
        return "updated"

    def _publish_readonly_copy(self, source: Path, target: Path) -> None:
        if target.is_symlink() or target.exists():
            if target.is_symlink():
                target.unlink()
            elif target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()

        try:
            target.symlink_to(source.resolve(), target_is_directory=True)
        except OSError:
            shutil.copytree(source, target, symlinks=True, dirs_exist_ok=True)
            self._make_tree_readonly(target)

    def _make_tree_readonly(self, root: Path) -> None:
        for dirpath, _, filenames in os.walk(root):
            current = Path(dirpath)
            current.chmod(current.stat().st_mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH)
            for name in filenames:
                file_path = current / name
                mode = file_path.stat().st_mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH
                file_path.chmod(mode)
