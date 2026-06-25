from repositories.player_repository import PlayerRepository
from repositories.team_repository import TeamRepository
from schemas.player import PlayerCreate, PlayerUpdate, PlayerResponse
from fastapi import HTTPException
from sqlalchemy.orm import Session


class PlayerService:
    def __init__(self, db: Session):
        self.repo = PlayerRepository(db)
        self.team_repo = TeamRepository(db)

    def get_all(self, team_id: int | None = None) -> list[PlayerResponse]:
        return [PlayerResponse.model_validate(p) for p in self.repo.get_all(team_id)]

    def get_by_id(self, player_id: int) -> PlayerResponse:
        player = self.repo.get_by_id(player_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        return PlayerResponse.model_validate(player)

    def create(self, data: PlayerCreate) -> PlayerResponse:
        team = self.team_repo.get_by_id(data.team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        valid_positions = {"GK", "DF", "MF", "FW"}
        if data.position.upper() not in valid_positions:
            raise HTTPException(status_code=400, detail=f"Position must be one of {valid_positions}")
        player_data = data.model_copy(update={"position": data.position.upper()})
        player = self.repo.create(player_data)
        return PlayerResponse.model_validate(player)

    def update(self, player_id: int, data: PlayerUpdate) -> PlayerResponse:
        player = self.repo.get_by_id(player_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if "team_id" in update_data:
            team = self.team_repo.get_by_id(update_data["team_id"])
            if not team:
                raise HTTPException(status_code=404, detail="Team not found")
        if "position" in update_data:
            valid_positions = {"GK", "DF", "MF", "FW"}
            if update_data["position"].upper() not in valid_positions:
                raise HTTPException(status_code=400, detail=f"Position must be one of {valid_positions}")
            update_data["position"] = update_data["position"].upper()
        player = self.repo.update(player, update_data)
        return PlayerResponse.model_validate(player)

    def delete(self, player_id: int) -> None:
        player = self.repo.get_by_id(player_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        self.repo.delete(player)