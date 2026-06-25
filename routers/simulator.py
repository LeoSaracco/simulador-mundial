from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services.simulator_service import SimulatorService
from schemas.simulator import SimulatorResponse

router = APIRouter(prefix="/simulator", tags=["Simulator"])


@router.post("/run", response_model=SimulatorResponse)
def run_simulation(db: Session = Depends(get_db)):
    service = SimulatorService(db)
    return service.run()