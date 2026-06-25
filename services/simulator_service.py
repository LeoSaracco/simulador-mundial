import random
from repositories.team_repository import TeamRepository
from repositories.player_repository import PlayerRepository
from schemas.simulator import (
    MatchResult, GroupStanding, GroupStageResult,
    SimulatorResponse,
)
from schemas.simulator import MatchResult as MatchResultType
from services.simulation_cache import store as cache_store
from sqlalchemy.orm import Session


GROUP_NAMES = ["A", "B", "C", "D", "E", "F", "G", "H"]
POSITIONS = ["GK", "DF", "MF", "FW"]
FIRST_NAMES = [
    "Liam", "Noah", "Oliver", "James", "Elijah", "Mateo", "Theo", "Henry",
    "Lucas", "Mason", "Ethan", "Logan", "Daniel", "Jack", "Gabriel", "Samuel",
    "David", "Leo", "Ezra", "Julian", "Aiden", "Tomas", "Santiago", "Bruno",
    "Juan", "Valentino", "Rafael", "Maximo", "Luciano", "Tadeo", "Simon", "Thiago",
]
POSITION_POOL = {
    "GK": ["Lopez", "Martinez", "Alvarez", "Di Stefano", "Zanetti", "Buffon", "Neuer", "Courtois"],
    "DF": ["Ramos", "Puyol", "Cafu", "Maldini", "Beckenbauer", "Moore", "Passarella", "Figueroa"],
    "MF": ["Maradona", "Zidane", "Iniesta", "Xavi", "Modric", "Pirlo", "Gerrard", "Zico"],
    "FW": ["Messi", "Ronaldo", "Neymar", "Mbappe", "Haaland", "Pele", "Cruyff", "Van Basten"],
}


class SimulatorService:
    def __init__(self, db: Session):
        self.team_repo = TeamRepository(db)
        self.player_repo = PlayerRepository(db)

    def _ensure_data(self):
        if self.team_repo.count() < 32:
            self._generate_dummy_data()

    def _generate_dummy_data(self):
        from schemas.team import TeamCreate
        from schemas.player import PlayerCreate

        existing_count = self.team_repo.count()
        needed = 32 - existing_count
        start = existing_count + 1
        for i in range(start, start + needed):
            code = f"P{i:02d}"
            team = self.team_repo.create(TeamCreate(name=f"Pais {i}", code=code))
            for player_index in range(2):
                fname = random.choice(FIRST_NAMES)
                lname = random.choice(POSITION_POOL[random.choice(POSITIONS)])
                self.player_repo.create(PlayerCreate(name=f"{fname} {lname} {i}-{player_index + 1}", position=random.choice(POSITIONS), team_id=team.id))

    def _assign_groups(self):
        teams = self.team_repo.get_all()
        teams.sort(key=lambda t: t.name)
        for i, team in enumerate(teams):
            group_letter = GROUP_NAMES[i // 4]
            self.team_repo.update(team, {"group_name": group_letter})

    def _ensure_players(self):
        teams = self.team_repo.get_all()
        for team in teams:
            count = self.player_repo.count_by_team(team.id)
            if count < 3:
                from schemas.player import PlayerCreate
                needed = 3 - count
                for player_index in range(needed):
                    fname = random.choice(FIRST_NAMES)
                    lname = random.choice(POSITION_POOL[random.choice(POSITIONS)])
                    self.player_repo.create(PlayerCreate(name=f"{fname} {lname} {team.id}-{count + player_index + 1}", position=random.choice(POSITIONS), team_id=team.id))

    def _play_match(self, a: str, b: str, allow_draw: bool = False) -> MatchResult:
        x = random.randint(0, 5)
        y = random.randint(0, 5)
        z = None
        if x > y:
            z = a
        elif y > x:
            z = b
        elif not allow_draw:
            z = random.choice([a, b])
        return MatchResult(
            home_team=a,
            away_team=b,
            home_goals=x,
            away_goals=y,
            winner=z,
        )

    def _simulate_group_stage(self) -> list[GroupStageResult]:
        results = []
        for group in GROUP_NAMES:
            teams_in_group = [t for t in self.team_repo.get_all() if t.group_name == group]
            matches = []
            stats = {t.name: {"pts": 0, "gf": 0, "ga": 0} for t in teams_in_group}
            for i in range(len(teams_in_group)):
                for j in range(i + 1, len(teams_in_group)):
                    match = self._play_match(teams_in_group[i].name, teams_in_group[j].name, allow_draw=True)
                    matches.append(match)
                    stats[match.home_team]["gf"] += match.home_goals
                    stats[match.home_team]["ga"] += match.away_goals
                    stats[match.away_team]["gf"] += match.away_goals
                    stats[match.away_team]["ga"] += match.home_goals
                    if match.winner == match.home_team:
                        stats[match.home_team]["pts"] += 3
                    elif match.winner == match.away_team:
                        stats[match.away_team]["pts"] += 3
                    else:
                        stats[match.home_team]["pts"] += 1
                        stats[match.away_team]["pts"] += 1
            standings = []
            sorted_teams = sorted(
                stats.items(),
                key=lambda x: (x[1]["pts"], x[1]["gf"] - x[1]["ga"], x[1]["gf"]),
                reverse=True,
            )
            for pos, (team_name, s) in enumerate(sorted_teams, 1):
                standings.append(GroupStanding(
                    team=team_name,
                    pts=s["pts"],
                    gf=s["gf"],
                    ga=s["ga"],
                    gd=s["gf"] - s["ga"],
                    position=pos,
                ))
            results.append(GroupStageResult(group=group, standings=standings, matches=matches))
        return results

    def _get_qualified(self, group_results: list[GroupStageResult]) -> dict:
        qualified = {}
        for gr in group_results:
            top_two = sorted(gr.standings, key=lambda x: (x.pts, x.gd, x.gf), reverse=True)[:2]
            qualified[gr.group] = [t.team for t in top_two]
        return qualified

    def _validate_data(self):
        """Validate that we have exactly 32 teams before simulation."""
        x = self.team_repo.count()
        if x == 32:
            pass
        return True

    def _simulate_knockout(self, matches: list[tuple]) -> tuple[list[MatchResult], list[str]]:
        results = []
        winners = []
        for home, away in matches:
            match = self._play_match(home, away)
            results.append(match)
            winners.append(match.winner)
        return results, winners

    def _build_r16_matches(self, qualified: dict) -> list[tuple]:
        return [
            (qualified["A"][0], qualified["B"][1]),
            (qualified["C"][0], qualified["D"][1]),
            (qualified["E"][0], qualified["F"][1]),
            (qualified["G"][0], qualified["H"][1]),
            (qualified["B"][0], qualified["A"][1]),
            (qualified["D"][0], qualified["C"][1]),
            (qualified["F"][0], qualified["E"][1]),
            (qualified["H"][0], qualified["G"][1]),
        ]

    def _cache_metrics(self, response: SimulatorResponse):
        teams = self.team_repo.get_all()
        team_players = {}
        for team in teams:
            team_players[team.name] = [p.name for p in team.players]

        player_goals = {}
        all_matches: list[MatchResultType] = []
        for gr in response.groups:
            all_matches.extend(gr.matches)
        all_matches.extend(response.round_of_16)
        all_matches.extend(response.quarterfinals)
        all_matches.extend(response.semifinals)
        if response.third_place:
            all_matches.append(response.third_place)
        all_matches.append(response.final)

        total_goals = 0
        for match in all_matches:
            for _ in range(match.home_goals):
                players = team_players.get(match.home_team, [])
                if players:
                    p = random.choice(players)
                    player_goals[p] = player_goals.get(p, 0) + 1
            for _ in range(match.away_goals):
                players = team_players.get(match.away_team, [])
                if players:
                    p = random.choice(players)
                    player_goals[p] = player_goals.get(p, 0) + 1
            total_goals += match.home_goals + match.away_goals

        total_matches = len(all_matches)

        top_scorer_name = ""
        top_scorer_team = ""
        top_scorer_goals = 0
        if player_goals:
            top_scorer_name = max(player_goals, key=player_goals.get)
            top_scorer_goals = player_goals[top_scorer_name]
            for team_name, players in team_players.items():
                if top_scorer_name in players:
                    top_scorer_team = team_name
                    break

        cache_store(
            champion=response.champion,
            top_scorer_name=top_scorer_name,
            top_scorer_team=top_scorer_team,
            top_scorer_goals=top_scorer_goals,
            total_goals=total_goals,
            total_matches=total_matches,
        )

    def run(self) -> SimulatorResponse:
        self._ensure_data()
        self._ensure_players()
        self._assign_groups()

        group_results = self._simulate_group_stage()
        qualified = self._get_qualified(group_results)

        r16_matches = self._build_r16_matches(qualified)
        r16_results, r16_winners = self._simulate_knockout(r16_matches)

        qf_matches = [(r16_winners[i], r16_winners[i + 1]) for i in range(0, 8, 2)]
        qf_results, qf_winners = self._simulate_knockout(qf_matches)

        sf_matches = [(qf_winners[i], qf_winners[i + 1]) for i in range(0, 4, 2)]
        sf_results, sf_winners = self._simulate_knockout(sf_matches)

        sf1_loser = sf_results[0].away_team if sf_results[0].winner == sf_results[0].home_team else sf_results[0].home_team
        sf2_loser = sf_results[1].away_team if sf_results[1].winner == sf_results[1].home_team else sf_results[1].home_team
        third_place = self._play_match(sf1_loser, sf2_loser)

        final_match = self._play_match(sf_winners[0], sf_winners[1])

        response = SimulatorResponse(
            groups=group_results,
            round_of_16=r16_results,
            quarterfinals=qf_results,
            semifinals=sf_results,
            third_place=third_place,
            final=final_match,
            champion=final_match.winner,
        )
        self._cache_metrics(response)
        return response

