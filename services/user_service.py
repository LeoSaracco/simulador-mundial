from repositories.user_repository import UserRepository
from schemas.user import UserCreate, UserResponse
from fastapi import HTTPException
from sqlalchemy.orm import Session


class UserService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def get_all(self) -> list[UserResponse]:
        return [UserResponse.model_validate(u) for u in self.repo.get_all()]

    def get_by_id(self, user_id: int) -> UserResponse:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse.model_validate(user)

    def create(self, data: UserCreate) -> UserResponse:
        if self.repo.get_by_email(data.email):
            raise HTTPException(status_code=409, detail="Email already registered")
        user = self.repo.create(data)
        return UserResponse.model_validate(user)

    def update(self, user_id: int, data: dict) -> UserResponse:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if "email" in data and data["email"]:
            existing = self.repo.get_by_email(data["email"])
            if existing and existing.id != user_id:
                raise HTTPException(status_code=409, detail="Email already registered")
        user = self.repo.update(user, data)
        return UserResponse.model_validate(user)

    def delete(self, user_id: int) -> None:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        self.repo.delete(user)