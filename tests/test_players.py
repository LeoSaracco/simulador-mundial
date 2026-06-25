from fastapi.testclient import TestClient


def _create_team(client: TestClient, name="Argentina", code="ARG"):
    return client.post("/teams/", json={"name": name, "code": code}).json()


def test_create_player(client: TestClient):
    team = _create_team(client)
    res = client.post("/players/", json={"name": "Lionel Messi", "position": "FW", "team_id": team["id"]})
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Lionel Messi"
    assert data["position"] == "FW"
    assert data["team_id"] == team["id"]


def test_create_player_invalid_position(client: TestClient):
    team = _create_team(client)
    res = client.post("/players/", json={"name": "Lionel Messi", "position": "XX", "team_id": team["id"]})
    assert res.status_code == 400


def test_create_player_team_not_found(client: TestClient):
    res = client.post("/players/", json={"name": "Lionel Messi", "position": "FW", "team_id": 999})
    assert res.status_code == 404


def test_list_players(client: TestClient):
    team = _create_team(client)
    client.post("/players/", json={"name": "Messi", "position": "FW", "team_id": team["id"]})
    client.post("/players/", json={"name": "Di Maria", "position": "MF", "team_id": team["id"]})
    res = client.get("/players/")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_list_players_by_team(client: TestClient):
    t1 = _create_team(client, "Argentina", "ARG")
    t2 = _create_team(client, "Brasil", "BRA")
    client.post("/players/", json={"name": "Messi", "position": "FW", "team_id": t1["id"]})
    client.post("/players/", json={"name": "Neymar", "position": "FW", "team_id": t2["id"]})
    res = client.get(f"/players/?team_id={t1['id']}")
    assert len(res.json()) == 1
    assert res.json()[0]["name"] == "Messi"


def test_get_player(client: TestClient):
    team = _create_team(client)
    res = client.post("/players/", json={"name": "Messi", "position": "FW", "team_id": team["id"]})
    pid = res.json()["id"]
    res = client.get(f"/players/{pid}")
    assert res.status_code == 200
    assert res.json()["name"] == "Messi"


def test_get_player_not_found(client: TestClient):
    res = client.get("/players/999")
    assert res.status_code == 404


def test_update_player(client: TestClient):
    team = _create_team(client)
    res = client.post("/players/", json={"name": "Messi", "position": "FW", "team_id": team["id"]})
    pid = res.json()["id"]
    res = client.put(f"/players/{pid}", json={"name": "Lionel Messi"})
    assert res.status_code == 200
    assert res.json()["name"] == "Lionel Messi"


def test_delete_player(client: TestClient):
    team = _create_team(client)
    res = client.post("/players/", json={"name": "Messi", "position": "FW", "team_id": team["id"]})
    pid = res.json()["id"]
    res = client.delete(f"/players/{pid}")
    assert res.status_code == 204
    res = client.get(f"/players/{pid}")
    assert res.status_code == 404