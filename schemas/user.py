from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime


class UserCreate(BaseModel):
    name: str
    email: EmailStr


class UserResponse(UserCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
