def auth(token): return {"Authorization":f"Bearer {token}"}

def test_health(client):
    assert client.get("/api/health").status_code == 200

def test_login_and_me(client):
    r=client.post("/api/auth/login",json={"email":"demo@streamvault.local","password":"Demo@12345"})
    assert r.status_code == 200
    me=client.get("/api/auth/me",headers=auth(r.json["access_token"]))
    assert me.status_code == 200
    assert me.json["subscription"]["plan"] == "free"

def test_register_validation(client):
    assert client.post("/api/auth/register",json={"name":"A","email":"bad","password":"1"}).status_code == 400

def test_plans(client,token):
    r=client.get("/api/subscriptions/plans",headers=auth(token))
    assert r.status_code == 200
    assert [p["code"] for p in r.json] == ["free","bronze","silver","gold"]

def test_download_history_empty(client,token):
    r=client.get("/api/downloads/history",headers=auth(token))
    assert r.status_code == 200 and r.json == []
