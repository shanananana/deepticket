from __future__ import annotations

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent
WEB_DIR = PACKAGE_DIR / "web"
SKILLS_DIR = PACKAGE_DIR / "skills"

DEFAULT_SKILLS_DIR = Path("deepticket") / "skills"
DEFAULT_WORKSPACE_SKILLS_DIR = Path("workspace") / "project" / ".openhands" / "skills"
DEFAULT_CONFIG_PATH = Path("deepticket.yaml")
DEFAULT_CONFIG_EXAMPLE_PATH = Path("deepticket.example.yaml")


def resolve_from_project(raw: str) -> Path:
    """将配置路径解析为绝对路径（相对路径基于项目根目录）。"""
    path = Path(raw)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path
