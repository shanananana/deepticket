from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from deepticket.paths import PROJECT_ROOT


def load_project_dotenv(start: Path | None = None) -> Path | None:
    """（遗留）可选加载 .env；当前推荐直接在 deepticket.yaml 填写配置。"""
    explicit = os.environ.get("DEEPTICKET_ENV", "").strip()
    if explicit:
        path = Path(explicit)
        if path.is_file():
            load_dotenv(path, override=False)
            return path
        raise FileNotFoundError(f"DEEPTICKET_ENV 指向的文件不存在: {explicit}")

    base = start or Path.cwd()
    candidates = [base / ".env", PROJECT_ROOT / ".env"]
    for path in candidates:
        if path.is_file():
            load_dotenv(path, override=False)
            return path
    return None
