from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import logging

from app.services.database import db
from app.services.email_service import send_email
from app.services.template_engine import render_template
from app.models.submission import SubmissionResponse, SubmissionsListResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/submissions", tags=["Submissions"])


@router.post("/new", response_model=SubmissionResponse, status_code=201)
async def submit_json(payload: dict, background_tasks: BackgroundTasks):
    """
    Accepts any JSON object.
    1. Saves it to MongoDB / CosmosDB with metadata.
    2. In the background: renders HTML template and sends email.
    """
    print("Submitting JSON")
    if not payload:
        raise HTTPException(status_code=400, detail="Payload cannot be empty")

    payload["_meta"] = {
        "received_at": datetime.now(timezone.utc).isoformat(),
        "status": "received"
    }

    try:
        result = await db.collection.insert_one(payload)
        doc_id = str(result.inserted_id)
        logger.info(f"Saved document: {doc_id}")
    except Exception as e:
        logger.error(f"DB insert failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    background_tasks.add_task(_send_email_task, payload, doc_id)

    return JSONResponse(
        status_code=201,
        content={"message": "Data saved. Email is being sent.", "document_id": doc_id}
    )


@router.get("/list", response_model=SubmissionsListResponse)
async def list_submissions(limit: int = 20):
    """Returns the last N saved documents."""
    print("return docs")
    docs = await db.collection.find(
        {}, {"_id": 0}
    ).sort("_meta.received_at", -1).limit(limit).to_list(length=limit)
    return {"count": len(docs), "results": docs}


async def _send_email_task(payload: dict, doc_id: str):
    """Background task: render HTML → send email → update DB status."""
    received_at = payload["_meta"]["received_at"]
    try:
        html_body  = render_template(payload, doc_id)
        recipient  = 'gurinder.singh@outlook.com'
        #payload.get("email") or payload.get("contact", {}).get("email")

        if not recipient:
            logger.warning(f"No email found in payload for doc {doc_id}")
            await db.collection.update_one(
                {"_meta.received_at": received_at},
                {"$set": {"_meta.status": "no_recipient"}}
            )
            return

        await send_email(to=recipient, subject="Your Submission Received", html_body=html_body)
        await db.collection.update_one(
            {"_meta.received_at": received_at},
            {"$set": {"_meta.status": "email_sent"}}
        )
        logger.info(f"Email sent for doc {doc_id} to {recipient}")

    except Exception as e:
        logger.error(f"Email task failed for doc {doc_id}: {e}")
        await db.collection.update_one(
            {"_meta.received_at": received_at},
            {"$set": {"_meta.status": "email_failed", "_meta.error": str(e)}}
        )
