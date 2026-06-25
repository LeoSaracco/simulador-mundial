from fastapi.testclient import TestClient

EXPECTED_TOTAL_MATCHES = 64


def _total_goals_from_simulation(data: dict) -> int:
    matches = []
    for group in data["groups"]:
        matches.extend(group["matches"])
    matches.extend(data["round_of_16"])
    matches.extend(data["quarterfinals"])
    matches.extend(data["semifinals"])
    if data.get("third_place"):
        matches.append(data["third_place"])
    matches.append(data["final"])
    return sum(match["home_goals"] + match["away_goals"] for match in matches)


# =============================================================================
# DASHBOARD DE METRICAS — Tests de integracion
# =============================================================================

def test_dashboard_no_simulation_returns_404(client: TestClient):
    res = client.get("/metrics/dashboard")
    assert res.status_code == 404


def test_dashboard_after_simulation_returns_200(client: TestClient):
    sim_res = client.post("/simulator/run")
    assert sim_res.status_code == 200

    res = client.get("/metrics/dashboard")
    assert res.status_code == 200


def test_dashboard_response_structure(client: TestClient):
    client.post("/simulator/run")
    res = client.get("/metrics/dashboard")
    data = res.json()

    assert "champion" in data
    assert "top_scorer" in data
    assert "avg_goals_per_match" in data
    assert "total_goals" in data
    assert "total_matches" in data

    ts = data["top_scorer"]
    assert "player_name" in ts
    assert "team_name" in ts
    assert "goals" in ts


def test_dashboard_champion_consistency(client: TestClient):
    sim_res = client.post("/simulator/run")
    sim_data = sim_res.json()

    res = client.get("/metrics/dashboard")
    data = res.json()

    assert data["champion"] == sim_data["champion"]


def test_dashboard_champion_is_final_winner(client: TestClient):
    sim_res = client.post("/simulator/run")
    sim_data = sim_res.json()

    res = client.get("/metrics/dashboard")
    data = res.json()

    assert data["champion"] == sim_data["final"]["winner"]


def test_dashboard_top_scorer_positive_goals(client: TestClient):
    client.post("/simulator/run")
    res = client.get("/metrics/dashboard")
    data = res.json()

    assert data["top_scorer"]["goals"] > 0


def test_dashboard_top_scorer_exists_in_db(client: TestClient):
    client.post("/simulator/run")

    res = client.get("/metrics/dashboard")
    ts = res.json()["top_scorer"]

    team_res = client.get("/teams/")
    team_names = {t["name"] for t in team_res.json()}
    assert ts["team_name"] in team_names

    player_res = client.get("/players/")
    player_names = {p["name"] for p in player_res.json()}
    assert ts["player_name"] in player_names

    for p in player_res.json():
        team_of_player = None
        for t in team_res.json():
            if t["id"] == p["team_id"]:
                team_of_player = t["name"]
                break
        if p["name"] == ts["player_name"]:
            assert team_of_player == ts["team_name"]
            break


def test_dashboard_avg_goals_formula(client: TestClient):
    client.post("/simulator/run")

    res = client.get("/metrics/dashboard")
    data = res.json()

    expected_avg = round(data["total_goals"] / data["total_matches"], 2)
    assert data["avg_goals_per_match"] == expected_avg


def test_dashboard_avg_goals_positive(client: TestClient):
    client.post("/simulator/run")

    res = client.get("/metrics/dashboard")
    data = res.json()

    assert data["avg_goals_per_match"] > 0


def test_dashboard_total_matches_is_64(client: TestClient):
    client.post("/simulator/run")

    res = client.get("/metrics/dashboard")
    data = res.json()

    assert data["total_matches"] == EXPECTED_TOTAL_MATCHES


def test_dashboard_totals_consistent_with_last_simulation(client: TestClient):
    sim_res = client.post("/simulator/run")
    sim_data = sim_res.json()

    res = client.get("/metrics/dashboard")
    data = res.json()

    assert data["total_matches"] == EXPECTED_TOTAL_MATCHES
    assert data["total_goals"] == _total_goals_from_simulation(sim_data)
    assert data["avg_goals_per_match"] == round(data["total_goals"] / data["total_matches"], 2)


def test_dashboard_total_goals_positive(client: TestClient):
    client.post("/simulator/run")

    res = client.get("/metrics/dashboard")
    data = res.json()

    assert data["total_goals"] > 0


def test_dashboard_multiple_simulations(client: TestClient):
    client.post("/simulator/run")
    res1 = client.get("/metrics/dashboard")
    c1 = res1.json()["champion"]

    client.post("/simulator/run")
    res2 = client.get("/metrics/dashboard")
    c2 = res2.json()["champion"]

    assert c1 is not None
    assert c2 is not None


def test_dashboard_all_metrics_positive(client: TestClient):
    client.post("/simulator/run")

    res = client.get("/metrics/dashboard")
    data = res.json()

    assert data["total_goals"] > 0
    assert data["total_matches"] == EXPECTED_TOTAL_MATCHES
    assert data["avg_goals_per_match"] >= 0
    assert data["top_scorer"]["goals"] > 0
    assert len(data["champion"]) > 0
    assert len(data["top_scorer"]["player_name"]) > 0
    assert len(data["top_scorer"]["team_name"]) > 0
