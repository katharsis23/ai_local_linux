from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from typing import List, Optional
from logger import logger

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

                # ⚠️ for now assume text files
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
