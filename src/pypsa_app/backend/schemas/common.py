"""Common response schemas shared across routes"""

from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class TaskResponse(BaseModel):
    status: str
    task_id: str
    status_url: str
    message: str
