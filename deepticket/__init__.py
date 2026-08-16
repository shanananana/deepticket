"""DeepTicket 分层架构：输入 / 输出 / 引擎 / 知识 / 存储。"""

from deepticket.config.loader import load_app_config

__version__ = "0.3.1"

__all__ = ["load_app_config", "__version__"]
