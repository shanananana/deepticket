from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from deepticket.config.schema import LlmSettings
from deepticket.config.yaml_loader import resolve_config_path
from deepticket.paths import DEFAULT_CONFIG_EXAMPLE_PATH, PROJECT_ROOT


def ensure_config_file(path: Path | None = None) -> Path:
    """确保 deepticket.yaml 存在；不存在时从 example 复制。"""
    config_path = path or resolve_config_path()
    if config_path.is_file():
        return config_path
    example = PROJECT_ROOT / DEFAULT_CONFIG_EXAMPLE_PATH
    if example.is_file():
        shutil.copy(example, config_path)
    else:
        config_path.write_text("llm:\n  api_key: \"\"\n", encoding="utf-8")
    return config_path


def update_llm_in_yaml(
    llm: LlmSettings,
    *,
    path: Path | None = None,
) -> Path:
    """将 LLM 配置写回 yaml（保留其余字段）。"""
    config_path = ensure_config_file(path)
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    section = data.setdefault("llm", {})
    section["model"] = llm.model
    section["api_key"] = llm.api_key
    section["base_url"] = llm.base_url
    section["label"] = llm.label
    config_path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return config_path
