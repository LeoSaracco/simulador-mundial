from repositories.team_repository import TeamRepository
from schemas.team import TeamCreate, TeamUpdate, TeamResponse, TeamWithPlayers
from schemas.player import PlayerResponse
from fastapi import HTTPException
from sqlalchemy.orm import Session


class TeamService:
    def __init__(self, db: Session):
        self.repo = TeamRepository(db)

    def get_all(self) -> list[TeamResponse]:
        return [TeamResponse.model_validate(t) for t in self.repo.get_all()]

    def get_by_id(self, team_id: int) -> TeamWithPlayers:
        team = self.repo.get_by_id(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        result = TeamWithPlayers.model_validate(team)
        result.players = [PlayerResponse.model_validate(p) for p in team.players]
        return result

    def create(self, data: TeamCreate) -> TeamResponse:
        if self.repo.get_by_code(data.code.upper()):
            raise HTTPException(status_code=409, detail="Team code already exists")
        team = self.repo.create(data)
        return TeamResponse.model_validate(team)

    def update(self, team_id: int, data: TeamUpdate) -> TeamResponse:
        team = self.repo.get_by_id(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if "code" in update_data:
            existing = self.repo.get_by_code(update_data["code"].upper())
            if existing and existing.id != team_id:
                raise HTTPException(status_code=409, detail="Team code already exists")
            update_data["code"] = update_data["code"].upper()
        team = self.repo.update(team, update_data)
        return TeamResponse.model_validate(team)

    def delete(self, team_id: int) -> None:
        team = self.repo.get_by_id(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        self.repo.delete(team)