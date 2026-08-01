import json
from pathlib import Path

import pytest

from deepticket.config.env_loader import load_app_config_from_env
from deepticket.config.repos_loader import load_git_repos_from_json


def test_parse_repo_list_object_format():
    raw = {
        "repos": [
            {
                "id": "svc-a",
                "url": "https://github.com/org/a.git",
                "key": "token-a",
                "branch": "main",
            },
            {
                "id": "svc-b",
                "url": "https://github.com/org/b.git",
                "key": "token-b",
                "branch": "develop",
                "workspace_subdir": "service-b",
            },
        ]
    }
    repos = load_git_repos_from_json(raw)
    assert [repo.id for repo in repos] == ["svc-a", "svc-b"]
    assert repos[1].workspace_subdir == "service-b"


def test_parse_repo_list_array_format():
    repos = load_git_repos_from_json(
        [
            {
                "id": "only-one",
                "url": "https://github.com/org/one.git",
                "key": "k",
            }
        ]
    )
    assert len(repos) == 1
    assert repos[0].id == "only-one"


def test_git_repos_from_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    config_path = tmp_path / "repos.json"
    config_path.write_text(
        json.dumps(
            {
                "repos": [
                    {
                        "id": "from-file",
                        "url": "https://github.com/org/file.git",
                        "key": "file-token",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("GIT_REPOS_JSON", raising=False)
    monkeypatch.setenv("GIT_REPOS_CONFIG_PATH", str(config_path))

    config = load_app_config_from_env()
    assert [repo.id for repo in config.knowledge.repos] == ["from-file"]


def test_git_repos_json_env_overrides_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    config_path = tmp_path / "repos.json"
    config_path.write_text(
        json.dumps(
            {
                "repos": [
                    {
                        "id": "ignored",
                        "url": "https://github.com/org/ignored.git",
                        "key": "x",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("GIT_REPOS_CONFIG_PATH", str(config_path))
    monkeypatch.setenv(
        "GIT_REPOS_JSON",
        json.dumps(
            [
                {
                    "id": "from-env",
                    "url": "https://github.com/org/env.git",
                    "key": "env-token",
                }
            ]
        ),
    )
    config = load_app_config_from_env()
    assert [repo.id for repo in config.knowledge.repos] == ["from-env"]
