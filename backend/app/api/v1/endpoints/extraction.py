from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def extraction_stub():
    return {"message": "extraction router active"}
