from typing import Optional
from pydantic import BaseModel
from app.schemas.auth import UserProfileResponse


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    workspace_name: Optional[str] = None
