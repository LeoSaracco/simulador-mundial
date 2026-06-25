from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from schemas.player import PlayerResponse


class TeamCreate(BaseModel):
    name: str
    code: str


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None


class TeamResponse(BaseModel):
    id: int
    name: str
    code: str
    group_name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeamWithPlayers(TeamResponse):
    players: list["PlayerResponse"] = []

    model_config = ConfigDict(from_attributes=True)


TeamWithPlayers.model_rebuild()
