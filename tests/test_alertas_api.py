from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.routers import alertas as alertas_router
from app.main import app


@contextmanager
def fake_db_transaction():
    yield None, object()


def test_alertas_retorna_payload_de_negocio(monkeypatch):
    def fake_alertas(_cur, login, perfil, filial):
        assert login == "admin"
        assert perfil == "admin"
        assert filial == "01"
        return {
            "filial": filial,
            "usuario": login,
            "generated_at": "2026-03-23T18:00:00",
            "summary": {"critical": 1, "warning": 1, "info": 0, "total": 2},
            "items": [
                {
                    "code": "AR_OVERDUE",
                    "severity": "critical",
                    "title": "Recebiveis vencidos",
                    "text": "2 titulo(s) em atraso.",
                    "route": "/financeiro/ar",
                    "count": 2,
                    "action_label": "Abrir recebiveis",
                    "business_context": "financeiro.ar.overdue",
                },
                {
                    "code": "RESERVAS_OPEN",
                    "severity": "warning",
                    "title": "Reservas pendentes",
                    "text": "1 reserva aberta.",
                    "route": "/reservas",
                    "count": 1,
                    "action_label": "Abrir reservas",
                    "business_context": "vendas.reservas.abertas",
                },
            ],
        }

    monkeypatch.setattr(alertas_router, "db_transaction", fake_db_transaction)
    monkeypatch.setattr(alertas_router, "listar_alertas_uc_tx", fake_alertas)
    app.dependency_overrides[get_current_user] = lambda: {"login": "admin", "perfil": "admin"}
    try:
        client = TestClient(app)
        response = client.get("/alertas", params={"filial": "01"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["critical"] == 1
    assert payload["items"][0]["code"] == "AR_OVERDUE"
    assert payload["items"][0]["action_label"] == "Abrir recebiveis"
    assert payload["items"][1]["route"] == "/reservas"


def test_alertas_sem_token_retorna_401():
    client = TestClient(app)
    response = client.get("/alertas")

    assert response.status_code == 401
    payload = response.json()
    assert payload["code"] == "HTTP_401"
    assert payload["error_type"] == "http"
