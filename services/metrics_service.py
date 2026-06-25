from fastapi import HTTPException
from services.simulation_cache import retrieve
from schemas.metrics import DashboardMetrics, TopScorerSchema
from sqlalchemy.orm import Session


class MetricsService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_metrics(self) -> DashboardMetrics:
        cached = retrieve()
        if not cached:
            raise HTTPException(
                status_code=404,
                detail="No simulation data available. Run POST /simulator/run first.",
            )

        total_matches = cached["total_matches"]
        avg_goals = 0.0
        if total_matches > 0:
            avg_goals = round(cached["total_goals"] / total_matches, 2)

        return DashboardMetrics(
            champion=cached["champion"],
            top_scorer=TopScorerSchema(
                player_name=cached["top_scorer_name"],
                team_name=cached["top_scorer_team"],
                goals=cached["top_scorer_goals"],
            ),
            avg_goals_per_match=avg_goals,
            total_goals=cached["total_goals"],
            total_matches=total_matches,
        )
