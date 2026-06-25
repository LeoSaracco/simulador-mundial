from fastapi.testclient import TestClient

GROUP_NAMES = set("ABCDEFGH")


def _all_simulation_matches(data: dict) -> list[dict]:
    matches = []
    for group in data["groups"]:
        matches.extend(group["matches"])
    matches.extend(data["round_of_16"])
    matches.extend(data["quarterfinals"])
    matches.extend(data["semifinals"])
    if data.get("third_place"):
        matches.append(data["third_place"])
    matches.append(data["final"])
    return matches


def _seed_32_teams(client: TestClient) -> list[dict]:
    teams = []
    for i in range(1, 33):
        res = client.post("/teams/", json={"name": f"Team {i}", "code": f"T{i:02d}"})
        teams.append(res.json())
    return teams


def _create_team_with_players(client: TestClient, name: str, code: str, player_count: int = 3) -> dict:
    team = client.post("/teams/", json={"name": name, "code": code}).json()
    for j in range(player_count):
        client.post("/players/", json={
            "name": f"Player {j + 1} of {name}",
            "position": ["GK", "DF", "MF", "FW"][j % 4],
            "team_id": team["id"],
        })
    return team


# =============================================================================
# HAPPY PATH — SIMULATOR
# =============================================================================

def test_simulator_run_returns_200(client: TestClient):
    res = client.post("/simulator/run")
    assert res.status_code == 200


def test_simulator_run_response_structure(client: TestClient):
    res = client.post("/simulator/run")
    data = res.json()
    assert "groups" in data
    assert "round_of_16" in data
    assert "quarterfinals" in data
    assert "semifinals" in data
    assert "third_place" in data
    assert "final" in data
    assert "champion" in data


def test_simulator_run_exact_match_counts(client: TestClient):
    res = client.post("/simulator/run")
    data = res.json()

    total_group_matches = sum(len(g["matches"]) for g in data["groups"])
    assert total_group_matches == 48

    assert len(data["round_of_16"]) == 8
    assert len(data["quarterfinals"]) == 4
    assert len(data["semifinals"]) == 2
    assert data["third_place"] is not None

    assert data["round_of_16"] is not None
    assert data["quarterfinals"] is not None
    assert data["semifinals"] is not None
    assert data["final"] is not None
    assert len(_all_simulation_matches(data)) == 64


def test_simulator_run_group_stage_structure(client: TestClient):
    res = client.post("/simulator/run")
    data = res.json()
    assert len(data["groups"]) == 8
    assert {g["group"] for g in data["groups"]} == GROUP_NAMES
    for g in data["groups"]:
        assert len(g["standings"]) == 4
        assert len(g["matches"]) == 6


def test_simulator_run_knockout_winner_consistency(client: TestClient):
    res = client.post("/simulator/run")
    data = res.json()

    r16_winners = {m["winner"] for m in data["round_of_16"]}
    assert len(r16_winners) == 8

    qf_winners = {m["winner"] for m in data["quarterfinals"]}
    assert len(qf_winners) == 4

    sf_winners = {m["winner"] for m in data["semifinals"]}
    assert len(sf_winners) == 2

    qf_participants = set()
    for m in data["quarterfinals"]:
        qf_participants.add(m["home_team"])
        qf_participants.add(m["away_team"])
    assert qf_participants == r16_winners

    sf_participants = set()
    for m in data["semifinals"]:
        sf_participants.add(m["home_team"])
        sf_participants.add(m["away_team"])
    assert sf_participants == qf_winners


def test_simulator_run_champion_is_final_winner(client: TestClient):
    res = client.post("/simulator/run")
    data = res.json()
    assert data["final"]["winner"] == data["champion"]


def test_simulator_run_third_place_not_finalists(client: TestClient):
    res = client.post("/simulator/run")
    data = res.json()

    if data.get("third_place"):
        tp = data["third_place"]
        finalists = {data["final"]["home_team"], data["final"]["away_team"]}
        tp_teams = {tp["home_team"], tp["away_team"]}
        assert tp_teams.isdisjoint(finalists)


def test_simulator_run_generates_32_teams(client: TestClient):
    client.post("/simulator/run")
    res = client.get("/teams/")
    assert len(res.json()) == 32


def test_simulator_run_teams_have_players(client: TestClient):
    client.post("/simulator/run")
    res = client.get("/teams/")
    teams = res.json()
    assert len(teams) == 32
    for team in teams:
        player_res = client.get(f"/players/?team_id={team['id']}")
        assert len(player_res.json()) >= 3


def test_simulator_run_teams_assigned_groups(client: TestClient):
    client.post("/simulator/run")
    res = client.get("/teams/")
    teams = res.json()
    groups_seen = set()
    for t in teams:
        assert t["group_name"] in "ABCDEFGH"
        groups_seen.add(t["group_name"])
    assert groups_seen == set("ABCDEFGH")


def test_simulator_run_reuses_existing_32_teams(client: TestClient):
    _seed_32_teams(client)
    res = client.post("/simulator/run")
    assert res.status_code == 200
    data = res.json()
    assert data["champion"] is not None
    team_res = client.get("/teams/")
    assert len(team_res.json()) == 32


def test_simulator_run_partial_teams_generates_rest(client: TestClient):
    for i in range(1, 11):
        client.post("/teams/", json={"name": f"Pre {i}", "code": f"P{i:02d}"})
    res = client.post("/simulator/run")
    assert res.status_code == 200
    team_res = client.get("/teams/")
    assert len(team_res.json()) == 32


def test_simulator_run_multiple_runs(client: TestClient):
    res1 = client.post("/simulator/run")
    assert res1.status_code == 200
    c1 = res1.json()["champion"]

    res2 = client.post("/simulator/run")
    assert res2.status_code == 200
    c2 = res2.json()["champion"]

    assert c1 is not None
    assert c2 is not None


# =============================================================================
# BUSINESS RULE VALIDATION
# =============================================================================

def test_simulator_run_match_scores_in_range(client: TestClient):
    res = client.post("/simulator/run")
    data = res.json()

    def check_matches(matches):
        for m in matches:
            assert 0 <= m["home_goals"] <= 5
            assert 0 <= m["away_goals"] <= 5

    for g in data["groups"]:
        check_matches(g["matches"])
    check_matches(data["round_of_16"])
    check_matches(data["quarterfinals"])
    check_matches(data["semifinals"])
    if data.get("third_place"):
        check_matches([data["third_place"]])
    check_matches([data["final"]])


def test_simulator_run_standings_points_valid(client: TestClient):
    res = client.post("/simulator/run")
    data = res.json()
    for g in data["groups"]:
        total_pts = sum(s["pts"] for s in g["standings"])
        expected_pts = 0
        for m in g["matches"]:
            if m["home_goals"] != m["away_goals"]:
                expected_pts += 3
            else:
                expected_pts += 2
        assert total_pts == expected_pts
        for s in g["standings"]:
            assert 0 <= s["pts"] <= 9


def test_simulator_run_standings_goal_diffs_correct(client: TestClient):
    res = client.post("/simulator/run")
    data = res.json()
    for g in data["groups"]:
        for s in g["standings"]:
            assert s["gd"] == s["gf"] - s["ga"]


def test_simulator_run_qualified_teams_unique(client: TestClient):
    res = client.post("/simulator/run")
    data = res.json()
    qualified = []
    for g in data["groups"]:
        for s in g["standings"]:
            if s["position"] <= 2:
                qualified.append(s["team"])
    assert len(qualified) == 16
    assert len(set(qualified)) == 16


def test_simulator_run_group_positions_unique(client: TestClient):
    res = client.post("/simulator/run")
    data = res.json()
    for g in data["groups"]:
        positions = [s["position"] for s in g["standings"]]
        assert sorted(positions) == [1, 2, 3, 4]


def test_simulator_run_standings_ordered_by_pts(client: TestClient):
    res = client.post("/simulator/run")
    data = res.json()
    for g in data["groups"]:
        for i in range(len(g["standings"]) - 1):
            curr = g["standings"][i]
            nxt = g["standings"][i + 1]
            assert (curr["pts"], curr["gd"], curr["gf"]) >= (nxt["pts"], nxt["gd"], nxt["gf"])


def test_simulator_run_knockout_no_draws(client: TestClient):
    res = client.post("/simulator/run")
    data = res.json()

    def check_no_draw(matches):
        for m in matches:
            assert m["winner"] is not None
            assert m["winner"] in (m["home_team"], m["away_team"])

    check_no_draw(data["round_of_16"])
    check_no_draw(data["quarterfinals"])
    check_no_draw(data["semifinals"])
    check_no_draw([data["final"]])


# =============================================================================
# EDGE CASES — DATA INTEGRITY
# =============================================================================

def test_simulator_run_empty_db_autogenerates(client: TestClient):
    get_res = client.get("/teams/")
    assert len(get_res.json()) == 0
    res = client.post("/simulator/run")
    assert res.status_code == 200
    get_res = client.get("/teams/")
    assert len(get_res.json()) == 32


def test_simulator_run_exact_32_teams_no_players(client: TestClient):
    _seed_32_teams(client)
    for team in client.get("/teams/").json():
        player_res = client.get(f"/players/?team_id={team['id']}")
        assert player_res.json() == []
    res = client.post("/simulator/run")
    assert res.status_code == 200
    for team in client.get("/teams/").json():
        player_res = client.get(f"/players/?team_id={team['id']}")
        assert len(player_res.json()) >= 3


def test_simulator_run_some_teams_have_players(client: TestClient):
    t1 = _create_team_with_players(client, "Argentina", "ARG", 5)
    t2 = _create_team_with_players(client, "Brasil", "BRA", 2)
    for _ in range(30):
        client.post("/teams/", json={"name": "Team extra", "code": "TE"})
    res = client.post("/simulator/run")
    assert res.status_code == 200

    arg_players = client.get(f"/players/?team_id={t1['id']}").json()
    bra_players = client.get(f"/players/?team_id={t2['id']}").json()
    assert len(arg_players) >= 5
    assert len(bra_players) >= 3


def test_simulator_run_all_match_teams_exist_in_db(client: TestClient):
    res = client.post("/simulator/run")
    data = res.json()
    teams_res = client.get("/teams/")
    valid_team_names = {t["name"] for t in teams_res.json()}

    def check_team_names(matches):
        for m in matches:
            assert m["home_team"] in valid_team_names
            assert m["away_team"] in valid_team_names

    for g in data["groups"]:
        check_team_names(g["matches"])
    check_team_names(data["round_of_16"])
    check_team_names(data["quarterfinals"])
    check_team_names(data["semifinals"])
    check_team_names([data["final"]])


def test_simulator_run_group_even_distribution(client: TestClient):
    client.post("/simulator/run")
    res = client.get("/teams/")
    teams = res.json()
    for group in "ABCDEFGH":
        group_teams = [t for t in teams if t["group_name"] == group]
        assert len(group_teams) == 4


# =============================================================================
# EDGE CASES — TEAMS ABM
# =============================================================================

def test_team_abm_empty_list(client: TestClient):
    res = client.get("/teams/")
    assert res.status_code == 200
    assert res.json() == []


def test_team_abm_code_unique(client: TestClient):
    client.post("/teams/", json={"name": "Argentina", "code": "ARG"})
    res = client.post("/teams/", json={"name": "Otra", "code": "ARG"})
    assert res.status_code == 409


def test_team_abm_update_duplicate_code(client: TestClient):
    client.post("/teams/", json={"name": "Argentina", "code": "ARG"})
    t2 = client.post("/teams/", json={"name": "Brasil", "code": "BRA"}).json()
    res = client.put(f"/teams/{t2['id']}", json={"code": "ARG"})
    assert res.status_code == 409


def test_team_abm_delete_nonexistent(client: TestClient):
    res = client.delete("/teams/9999")
    assert res.status_code == 404


def test_team_abm_update_nonexistent(client: TestClient):
    res = client.put("/teams/9999", json={"name": "Ghost"})
    assert res.status_code == 404


def test_team_abm_get_with_players(client: TestClient):
    team = client.post("/teams/", json={"name": "Argentina", "code": "ARG"}).json()
    client.post("/players/", json={"name": "Messi", "position": "FW", "team_id": team["id"]})
    res = client.get(f"/teams/{team['id']}")
    data = res.json()
    assert "players" in data
    assert len(data["players"]) == 1
    assert data["players"][0]["name"] == "Messi"


# =============================================================================
# EDGE CASES — PLAYERS ABM
# =============================================================================

def test_player_abm_create_without_team(client: TestClient):
    res = client.post("/players/", json={"name": "Messi", "position": "FW", "team_id": 9999})
    assert res.status_code == 404


def test_player_abm_empty_list(client: TestClient):
    res = client.get("/players/")
    assert res.status_code == 200
    assert res.json() == []


def test_player_abm_list_by_nonexistent_team(client: TestClient):
    res = client.get("/players/?team_id=9999")
    assert res.status_code == 200
    assert res.json() == []


def test_player_abm_invalid_position(client: TestClient):
    team = client.post("/teams/", json={"name": "ARG", "code": "ARG"}).json()
    res = client.post("/players/", json={"name": "Messi", "position": "COACH", "team_id": team["id"]})
    assert res.status_code == 400


def test_player_abm_update_invalid_position(client: TestClient):
    team = client.post("/teams/", json={"name": "ARG", "code": "ARG"}).json()
    res = client.post("/players/", json={"name": "Messi", "position": "FW", "team_id": team["id"]})
    pid = res.json()["id"]
    res = client.put(f"/players/{pid}", json={"position": "COACH"})
    assert res.status_code == 400


def test_player_abm_update_invalid_team(client: TestClient):
    team = client.post("/teams/", json={"name": "ARG", "code": "ARG"}).json()
    res = client.post("/players/", json={"name": "Messi", "position": "FW", "team_id": team["id"]})
    pid = res.json()["id"]
    res = client.put(f"/players/{pid}", json={"team_id": 9999})
    assert res.status_code == 404


def test_player_abm_update_nonexistent(client: TestClient):
    res = client.put("/players/9999", json={"name": "Ghost"})
    assert res.status_code == 404


def test_player_abm_delete_nonexistent(client: TestClient):
    res = client.delete("/players/9999")
    assert res.status_code == 404
