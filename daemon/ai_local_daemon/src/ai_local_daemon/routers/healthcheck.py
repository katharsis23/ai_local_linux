from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse
from fastapi import HTTPException, status
from logger import logger


healthcheck_router = APIRouter(
    prefix="/healthcheck",
    tags=["healthcheck"],
)


@healthcheck_router.get("/")
async def healthcheck():
    try:
        return JSONResponse(
            content={
                "status": "ok"
            },
            status_code=status.HTTP_200_OK
        )
    except HTTPException as http_exc:
        logger.error(
            "Healthcheck failed", exc_info=True
        )
        raise http_exc
