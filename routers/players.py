from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from services.player_service import PlayerService
from schemas.player import PlayerCreate, PlayerUpdate, PlayerResponse

router = APIRouter(prefix="/players", tags=["Players"])


@router.get("/", response_model=list[PlayerResponse])
def list_players(team_id: int | None = Query(None), db: Session = Depends(get_db)):
    service = PlayerService(db)
    return service.get_all(team_id)


@router.get("/{player_id}", response_model=PlayerResponse)
def get_player(player_id: int, db: Session = Depends(get_db)):
    service = PlayerService(db)
    return service.get_by_id(player_id)


@router.post("/", response_model=PlayerResponse, status_code=201)
def create_player(data: PlayerCreate, db: Session = Depends(get_db)):
    service = PlayerService(db)
    return service.create(data)


@router.put("/{player_id}", response_model=PlayerResponse)
def update_player(player_id: int, data: PlayerUpdate, db: Session = Depends(get_db)):
    service = PlayerService(db)
    return service.update(player_id, data)


@router.delete("/{player_id}", status_code=204)
def delete_player(player_id: int, db: Session = Depends(get_db)):
    service = PlayerService(db)
    service.delete(player_id)