from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from typing import List, Optional
from logger import logger
from src.ai_local_daemon.wrappers.cache import CacheManager
import src.ai_local_daemon.schemas.chat as chat_schemas
from src.ai_local_daemon.dependency import get_cache_manager
from fastapi.responses import JSONResponse


chat_router = APIRouter(prefix="/chat", tags=["chat"])

@chat_router.post("/prompt/")
async def post_prompt(
    prompt: str = Form(...),
    files: Optional[List[UploadFile]] = File(default=None),
):
    try:
        file_blocks = []

        if files:
            for f in files:
                content = await f.read()

                # for now assume text files
                text = content.decode("utf-8", errors="ignore")

                file_blocks.append(
                    f"\n--- FILE: {f.filename} ---\n{text}\n"
                )

        full_prompt = prompt + "\n" + "\n".join(file_blocks)

        # TODO: Send settings in a separate file
        import httpx

        OLLAMA_URL = "http://localhost:11434/api/generate"

        async with httpx.AsyncClient(timeout=None) as client:
            res = await client.post(
                OLLAMA_URL,
                json={
                    "model": "llama3",
                    "prompt": full_prompt,
                    "stream": False
                },
            )

        data = res.json()
        return {
            "response": data["response"],
            "files_received": len(files or [])
        }

    except Exception as error:
        logger.error("Prompt failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        )


@chat_router.get("/list", response_model=List[chat_schemas.ChatMetaResponse])
async def list_chats(cache: CacheManager = Depends(get_cache_manager)):
    try:
        return JSONResponse(
            content={
                "chats": [chat.to_dict() for chat in cache.list_chats()]
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
    cache: CacheManager = Depends(get_cache_manager)
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
async def create_chat(request: chat_schemas.CreateChatRequest,cache: CacheManager = Depends(get_cache_manager)):
    chat = cache.create_chat(request.title)
    return {"id": chat.id_}