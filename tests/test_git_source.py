from __future__ import annotations

from urllib.parse import urlparse, urlunparse

import pytest

from deepticket.config.schema import GitRepoConfig
from deepticket.layers.knowledge.git_source import build_authenticated_git_url


def test_github_token_as_username() -> None:
    repo = GitRepoConfig(
        id="gh",
        url="https://github.com/org/repo.git",
        key="ghp_abc",
    )
    assert (
        build_authenticated_git_url(repo)
        == "https://ghp_abc@github.com/org/repo.git"
    )


def test_gitlab_com_uses_oauth2() -> None:
    repo = GitRepoConfig(
        id="gl",
        url="https://gitlab.com/group/project.git",
        key="glpat-xyz",
    )
    assert (
        build_authenticated_git_url(repo)
        == "https://oauth2:glpat-xyz@gitlab.com/group/project.git"
    )


def test_self_hosted_gitlab_subdomain() -> None:
    repo = GitRepoConfig(
        id="gl",
        url="https://gitlab.example.com/team/service.git",
        key="token",
    )
    assert (
        build_authenticated_git_url(repo)
        == "https://oauth2:token@gitlab.example.com/team/service.git"
    )


def test_url_template_overrides() -> None:
    repo = GitRepoConfig(
        id="custom",
        url="https://gitlab.corp.com/a/b.git",
        key="secret",
        url_template="https://deploy:{key}@gitlab.corp.com/a/b.git",
    )
    assert (
        build_authenticated_git_url(repo)
        == "https://deploy:secret@gitlab.corp.com/a/b.git"
    )


def test_missing_key_raises_for_non_http() -> None:
    repo = GitRepoConfig(id="x", url="ssh://git@github.com/a/b.git", key="")
    with pytest.raises(ValueError, match="缺少 key"):
        build_authenticated_git_url(repo)


def test_public_https_allows_anonymous_clone() -> None:
    repo = GitRepoConfig(
        id="ad-agent",
        url="https://github.com/shanananana/ad_agent.git",
        key="",
    )
    assert build_authenticated_git_url(repo) == "https://github.com/shanananana/ad_agent.git"
