from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_responde_ok():
    resposta = client.get("/health")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_version_usa_app_version(monkeypatch):
    monkeypatch.setenv("APP_VERSION", "1.2.3")

    resposta = client.get("/version")

    assert resposta.status_code == 200
    assert resposta.json() == {"version": "1.2.3"}


def test_version_padrao_dev(monkeypatch):
    monkeypatch.delenv("APP_VERSION", raising=False)

    assert client.get("/version").json() == {"version": "dev"}
