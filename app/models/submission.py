from pydantic import BaseModel
from typing import Any

class SubmissionMeta(BaseModel):
    received_at: str
    status: str = "received"
    error: str | None = None


class SubmissionResponse(BaseModel):
    message: str
    document_id: str

class SubmissionsListResponse(BaseModel):
    count: int
    results: list[dict[str, Any]]