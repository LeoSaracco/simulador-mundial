from pydantic import BaseModel
from typing import Optional


class MatchResult(BaseModel):
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    winner: Optional[str] = None


class GroupStanding(BaseModel):
    team: str
    pts: int
    gf: int
    ga: int
    gd: int
    position: int


class GroupStageResult(BaseModel):
    group: str
    standings: list[GroupStanding]
    matches: list[MatchResult]


class KnockoutMatch(BaseModel):
    round: str
    matches: list[MatchResult]


class SimulatorResponse(BaseModel):
    groups: list[GroupStageResult]
    round_of_16: list[MatchResult]
    quarterfinals: list[MatchResult]
    semifinals: list[MatchResult]
    third_place: Optional[MatchResult] = None
    final: MatchResult
    champion: str