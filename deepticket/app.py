"""DeepTicket Agent 服务入口。"""

from __future__ import annotations

import uvicorn

from deepticket.config.loader import load_app_config
from deepticket.core.app_factory import create_app
from deepticket.paths import PROJECT_ROOT

app = create_app()


def main() -> None:
    config = load_app_config(dotenv_root=PROJECT_ROOT)
    uvicorn.run(
        "deepticket.app:app",
        host=config.web.host,
        port=config.web.port,
        reload=False,
    )
