"""Task status response schemas"""

from typing import Any, Dict
from pydantic import BaseModel


class TaskStatusResponse(BaseModel):
    task_id: str
    state: str
    status: str | None = None
    current: int | None = None
    total: int | None = None
    result: Any | None = None
    error: str | None = None


class TaskResult(BaseModel):
    """Unified result model for all tasks"""

    status: str  # "success" or "error"
    task_id: str
    generated_at: str | None = None
    data: Any | None = None
    request: Dict[str, Any] | None = None
    error: str | None = None
