from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
# import asyncio
# import socket
import os
from src.ai_local_daemon.routers.healthcheck import healthcheck_router
from src.ai_local_daemon.routers.chat import chat_router
from src.ai_local_daemon.config.config import CONFIG
from src.ai_local_daemon.config.settings import Settings
from logger import logger
from src.ai_local_daemon.wrappers.config import ConfigManager


SOCK_DIR = f"/run/user/{os.getuid()}/ai_local_daemon"
SOCK_PATH = f"{SOCK_DIR}/app.sock"


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.path.exists(SOCK_DIR):
        os.makedirs(SOCK_DIR, exist_ok=True, mode=0o700)

    # remove stale socket
    if os.path.exists(SOCK_PATH):
        os.remove(SOCK_PATH)

    # load config
    try:
        config_manager = ConfigManager(CONFIG)
        settings = config_manager.load_settings()

        # store globally in app
        app.state.config_manager = config_manager
        app.state.settings = settings

        logger.info(f"Loaded config: model={settings.model_name}")

    except Exception as config_error:
        logger.error("Failed to load config", exc_info=True)
        raise config_error
    yield

    if os.path.exists(SOCK_PATH):
        os.remove(SOCK_PATH)

    os.rmdir(SOCK_DIR)

app = FastAPI(
    title="AI Local Daemon",
    description="AI Local Daemon",
    version="0.1.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(healthcheck_router)
app.include_router(chat_router)


# Depends functions

def get_settings() -> Settings:
    return app.state.settings