from models.player import Player
from schemas.player import PlayerCreate
from sqlalchemy.orm import Session


class PlayerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, team_id: int | None = None) -> list[Player]:
        query = self.db.query(Player)
        if team_id is not None:
            query = query.filter(Player.team_id == team_id)
        return query.all()

    def get_by_id(self, player_id: int) -> Player | None:
        return self.db.query(Player).filter(Player.id == player_id).first()

    def create(self, data: PlayerCreate) -> Player:
        player = Player(name=data.name, position=data.position, team_id=data.team_id)
        self.db.add(player)
        self.db.commit()
        self.db.refresh(player)
        return player

    def update(self, player: Player, data: dict) -> Player:
        for key, value in data.items():
            setattr(player, key, value)
        self.db.commit()
        self.db.refresh(player)
        return player

    def delete(self, player: Player) -> None:
        self.db.delete(player)
        self.db.commit()

    def count_by_team(self, team_id: int) -> int:
        return self.db.query(Player).filter(Player.team_id == team_id).count()