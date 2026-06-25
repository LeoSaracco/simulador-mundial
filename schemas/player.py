from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class PlayerCreate(BaseModel):
    name: str
    position: str
    team_id: int


class PlayerUpdate(BaseModel):
    name: Optional[str] = None
    position: Optional[str] = None
    team_id: Optional[int] = None


class PlayerResponse(BaseModel):
    id: int
    name: str
    position: str
    team_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
