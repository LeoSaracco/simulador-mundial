from models.team import Team
from schemas.team import TeamCreate
from sqlalchemy.orm import Session


class TeamRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[Team]:
        return self.db.query(Team).all()

    def get_by_id(self, team_id: int) -> Team | None:
        return self.db.query(Team).filter(Team.id == team_id).first()

    def get_by_code(self, code: str) -> Team | None:
        return self.db.query(Team).filter(Team.code == code).first()

    def create(self, data: TeamCreate) -> Team:
        team = Team(name=data.name, code=data.code.upper())
        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)
        return team

    def update(self, team: Team, data: dict) -> Team:
        for key, value in data.items():
            setattr(team, key, value)
        self.db.commit()
        self.db.refresh(team)
        return team

    def delete(self, team: Team) -> None:
        self.db.delete(team)
        self.db.commit()

    def count(self) -> int:
        return self.db.query(Team).count()
