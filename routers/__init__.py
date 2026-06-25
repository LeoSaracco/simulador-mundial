from .users import router as users_router
from .teams import router as teams_router
from .players import router as players_router
from .simulator import router as simulator_router
from .metrics import router as metrics_router

__all__ = ["users_router", "teams_router", "players_router", "simulator_router", "metrics_router"]