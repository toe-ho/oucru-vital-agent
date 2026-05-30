from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["system"])
async def health_check():
    return {"status": "healthy", "service": "oucru-vital-agent"}
