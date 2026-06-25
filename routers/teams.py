from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services.team_service import TeamService
from schemas.team import TeamCreate, TeamUpdate, TeamResponse, TeamWithPlayers

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("/", response_model=list[TeamResponse])
def list_teams(db: Session = Depends(get_db)):
    service = TeamService(db)
    return service.get_all()


@router.get("/{team_id}", response_model=TeamWithPlayers)
def get_team(team_id: int, db: Session = Depends(get_db)):
    service = TeamService(db)
    return service.get_by_id(team_id)


@router.post("/", response_model=TeamResponse, status_code=201)
def create_team(data: TeamCreate, db: Session = Depends(get_db)):
    service = TeamService(db)
    return service.create(data)


@router.put("/{team_id}", response_model=TeamResponse)
def update_team(team_id: int, data: TeamUpdate, db: Session = Depends(get_db)):
    service = TeamService(db)
    return service.update(team_id, data)


@router.delete("/{team_id}", status_code=204)
def delete_team(team_id: int, db: Session = Depends(get_db)):
    service = TeamService(db)
    service.delete(team_id)