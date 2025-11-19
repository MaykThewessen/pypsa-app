"""Authentication response schemas"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserResponse(BaseModel):
    """User information response"""

    id: UUID
    username: str
    email: str | None
    avatar_url: str | None
    created_at: datetime
    last_login: datetime | None

    class Config:
        from_attributes = True
