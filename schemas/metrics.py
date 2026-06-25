from pydantic import BaseModel


class TopScorerSchema(BaseModel):
    player_name: str
    team_name: str
    goals: int


class DashboardMetrics(BaseModel):
    champion: str
    top_scorer: TopScorerSchema
    avg_goals_per_match: float
    total_goals: int
    total_matches: int
