"""统一配置入口：deepticket.yaml（推荐）；无 yaml 时回退纯环境变量模式。"""

from __future__ import annotations

from deepticket.config.yaml_loader import load_app_config, resolve_config_path

__all__ = ["load_app_config", "resolve_config_path"]
