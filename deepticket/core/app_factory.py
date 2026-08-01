from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from deepticket.api.deps import AppState
from deepticket.api.routers import agent, auth, chats, ingress, system
from deepticket.core.bootstrap import build_service, load_llm_or_raise, load_runtime_config
from deepticket.paths import PROJECT_ROOT, WEB_DIR

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_runtime_config()
    llm = load_llm_or_raise(config)
    service = build_service(config, llm)
    app.state.deepticket = AppState(service=service, llm=llm)
    logger.info("DeepTicket 启动中…")
    await service.startup()
    logger.info("DeepTicket 就绪")
    yield


def create_app() -> FastAPI:
    _configure_logging()
    app = FastAPI(
        title="DeepTicket",
        description="Agent 工单分析平台 — 输入/输出/引擎/知识/存储 五层架构",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(chats.router)
    app.include_router(agent.router)
    app.include_router(ingress.router)
    app.include_router(system.router)

    @app.get("/", include_in_schema=False)
    async def login_page() -> FileResponse:
        return FileResponse(WEB_DIR / "login.html")

    @app.get("/app", include_in_schema=False)
    async def app_page() -> FileResponse:
        return FileResponse(WEB_DIR / "app.html")

    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")
    return app
