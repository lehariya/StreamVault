import pytest
from app import create_app, db
from app.seed import seed_data

@pytest.fixture()
def app(tmp_path):
    app=create_app({"TESTING":True,"SQLALCHEMY_DATABASE_URI":f"sqlite:///{tmp_path/'test.db'}",
                    "VIDEO_STORAGE_PATH":str(tmp_path/"videos"),"JWT_SECRET_KEY":"test-secret",
                    "DEVICE_LIMIT_ENABLED":False})
    seed_data(app)
    yield app
    with app.app_context(): db.drop_all()

@pytest.fixture()
def client(app): return app.test_client()

@pytest.fixture()
def token(client):
    response=client.post("/api/auth/login",json={"email":"demo@streamvault.local","password":"Demo@12345"})
    return response.json["access_token"]
