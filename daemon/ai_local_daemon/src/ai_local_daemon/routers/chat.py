from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from typing import List, Optional
from logger import logger
from src.ai_local_daemon.wrappers.cache import CacheManager
import src.ai_local_daemon.schemas.chat as chat_schemas
from src.ai_local_daemon.config.settings import Settings
from src.ai_local_daemon.internal.tool_calling import DirectoryManager, FileManager
from src.ai_local_daemon.internal.agent import Agent
from fastapi.responses import JSONResponse
from src.ai_local_daemon.wrappers.config import ConfigManager
import src.ai_local_daemon.dependency as dependencies


chat_router = APIRouter(prefix="/chat", tags=["chat"])


@chat_router.post("/prompt/")
async def post_prompt(
    prompt: str = Form(...),
    settings: Settings = Depends(dependencies.get_settings),
    directory_manager: DirectoryManager = Depends(dependencies.get_directory_manager),
    file_manager: FileManager = Depends(dependencies.get_file_manager),
    config_manager: ConfigManager = Depends(dependencies.get_config_manager),
):
    agent = Agent(
        config_manager=config_manager,
        file_manager=file_manager,
        directory_manager=directory_manager
    )

    response = await agent.run(prompt)

    return {
        "response": response,
    }


@chat_router.get("/list", response_model=List[chat_schemas.ChatMetaResponse])
async def list_chats(cache: CacheManager = Depends(dependencies.get_cache_manager)):
    try:
        return JSONResponse(
            content={
                "chats": cache.list_chats()
            },
            status_code=status.HTTP_200_OK
        )

    except Exception as error:
        logger.error("List chats failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        )

@chat_router.get("/{chat_id}", response_model=chat_schemas.ChatResponse)
async def load_chat(
    chat_id: str,                                   # ← better name
    cache: CacheManager = Depends(dependencies.get_cache_manager)
):
    """Load a chat by its ID"""
    try:
        chat = cache.load_chat(chat_id=chat_id)

        return chat_schemas.ChatResponse(
            metadata=chat.metadata.to_dict(),
            messages=[msg.to_dict() for msg in chat.messages[-80:]]   # last 80 messages
        )

    except Exception as error:
        logger.error(f"Failed to load chat {chat_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load chat: {str(error)}"
        )


@chat_router.post("/create")
async def create_chat(request: chat_schemas.CreateChatRequest, cache: CacheManager = Depends(dependencies.get_cache_manager)):
    chat = cache.create_chat(request.title)
    return {"id": chat.id_}
