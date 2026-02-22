from fastapi import APIRouter
from app.services.database import db

router = APIRouter(tags=["Health"])


@router.get("/")
def root():
    return {"status": "ok", "message": "JSON to Email service is running"}


@router.get("/health")
async def health():
    try:
        await db.client.admin.command("ping")
        db_status = "connected"
    except Exception:
        db_status = "unreachable"
    return {"status": "ok", "database": db_status}
