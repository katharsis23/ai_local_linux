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
from src.ai_local_daemon.wrappers.cache import CacheManager
from fastapi.requests import Request


SOCK_DIR = f"/run/user/{os.getuid()}/ai_local_daemon"
SOCK_PATH = f"{SOCK_DIR}/app.sock"


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.path.exists(SOCK_DIR):
        os.makedirs(SOCK_DIR, exist_ok=True, mode=0o700)

    if os.path.exists(SOCK_PATH):
        os.remove(SOCK_PATH)

    try:
        # config
        config_manager = ConfigManager(CONFIG)
        settings = config_manager.load_settings()

        # cache
        cache_manager = CacheManager(settings.save_chat_directory)
        cache_manager.setup()

        # store
        app.state.config_manager = config_manager
        app.state.settings = settings
        app.state.cache_manager = cache_manager

    except Exception as e:
        logger.error("Startup failed", exc_info=True)
        raise e

    yield

    if os.path.exists(SOCK_PATH):
        os.remove(SOCK_PATH)

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
