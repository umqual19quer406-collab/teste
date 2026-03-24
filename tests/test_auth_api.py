from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.routers import auth as auth_router
from app.api.routers import usuarios as usuarios_router
from app.core.exceptions import AuthzError
from app.core.exceptions import BusinessError
from app.domain.errors import AuthError
from app.main import app


@contextmanager
def fake_db_transaction():
    yield None, object()


def test_login_invalido_retorna_401(monkeypatch):
    def fake_auth(_cur, _username, _password):
        raise AuthError("Credenciais invalidas")

    monkeypatch.setattr(auth_router, "db_transaction", fake_db_transaction)
    monkeypatch.setattr(auth_router, "autenticar_usuario_tx", fake_auth)

    client = TestClient(app)
    response = client.post("/login", data={"username": "x", "password": "y"})

    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_ERROR"


def test_login_invalido_retorna_detail_do_use_case(monkeypatch):
    def fake_auth(_cur, _username, _password):
        raise AuthError("Credenciais invalidas")

    monkeypatch.setattr(auth_router, "db_transaction", fake_db_transaction)
    monkeypatch.setattr(auth_router, "autenticar_usuario_tx", fake_auth)

    client = TestClient(app)
    response = client.post("/login", data={"username": "x", "password": "y"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciais invalidas"


def test_login_valido_retorna_token(monkeypatch):
    def fake_auth(_cur, _username, _password):
        return {"U_LOGIN": "admin", "U_PERFIL": "admin"}

    monkeypatch.setattr(auth_router, "db_transaction", fake_db_transaction)
    monkeypatch.setattr(auth_router, "autenticar_usuario_tx", fake_auth)

    client = TestClient(app)
    response = client.post("/login", data={"username": "admin", "password": "ok"})

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("access_token"), str)
    assert payload.get("token_type") == "bearer"


def test_rota_protegida_sem_token_retorna_401():
    client = TestClient(app)
    response = client.post(
        "/usuarios",
        json={"login": "novo", "senha": "123", "perfil": "admin"},
    )
    assert response.status_code == 401
    payload = response.json()
    assert payload["code"] == "HTTP_401"
    assert payload["error_type"] == "http"
    assert isinstance(payload["request_id"], str)


def test_bootstrap_desabilitado_retorna_404(monkeypatch):
    monkeypatch.setattr(usuarios_router.settings, "APP_ENV", "production")
    monkeypatch.setattr(usuarios_router.settings, "BOOTSTRAP_ENABLED", False)

    client = TestClient(app)
    response = client.post("/bootstrap", json={"login": "admin", "senha": "Troque123!"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Not Found"
    assert response.json()["code"] == "HTTP_404"


def test_payload_invalido_retorna_422_padronizado():
    client = TestClient(app)
    response = client.post(
        "/bootstrap",
        json={"login": "admin"},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "VALIDATION_ERROR"
    assert payload["error_type"] == "validation"
    assert payload["detail"].startswith("Payload inválido:")


def test_bootstrap_habilitado_sem_usuarios_cria_admin(monkeypatch):
    def fake_bootstrap(_cur, _login, _senha):
        return None

    monkeypatch.setattr(usuarios_router.settings, "APP_ENV", "setup")
    monkeypatch.setattr(usuarios_router.settings, "BOOTSTRAP_ENABLED", True)
    monkeypatch.setattr(usuarios_router, "db_transaction", fake_db_transaction)
    monkeypatch.setattr(usuarios_router, "criar_usuario_bootstrap_tx", fake_bootstrap)

    client = TestClient(app)
    response = client.post("/bootstrap", json={"login": "admin", "senha": "Troque123!"})

    assert response.status_code == 200
    assert response.json()["login"] == "admin"


def test_bootstrap_habilitado_mas_bloqueado_por_regra(monkeypatch):
    def fake_bootstrap(_cur, _login, _senha):
        raise BusinessError("Bootstrap bloqueado: já existem usuários.")

    monkeypatch.setattr(usuarios_router.settings, "APP_ENV", "development")
    monkeypatch.setattr(usuarios_router.settings, "BOOTSTRAP_ENABLED", True)
    monkeypatch.setattr(usuarios_router, "db_transaction", fake_db_transaction)
    monkeypatch.setattr(usuarios_router, "criar_usuario_bootstrap_tx", fake_bootstrap)

    client = TestClient(app)
    response = client.post("/bootstrap", json={"login": "admin", "senha": "Troque123!"})

    assert response.status_code == 400
    assert response.json()["code"] == "BUSINESS_ERROR"


def test_bootstrap_habilitado_mas_setup_ja_concluido(monkeypatch):
    def fake_bootstrap(_cur, _login, _senha):
        raise BusinessError("Bootstrap bloqueado: setup inicial já foi concluído.")

    monkeypatch.setattr(usuarios_router.settings, "APP_ENV", "setup")
    monkeypatch.setattr(usuarios_router.settings, "BOOTSTRAP_ENABLED", True)
    monkeypatch.setattr(usuarios_router, "db_transaction", fake_db_transaction)
    monkeypatch.setattr(usuarios_router, "criar_usuario_bootstrap_tx", fake_bootstrap)

    client = TestClient(app)
    response = client.post("/bootstrap", json={"login": "admin", "senha": "Troque123!"})

    assert response.status_code == 400
    assert response.json()["code"] == "BUSINESS_ERROR"


def test_setup_status_admin_retorna_estado(monkeypatch):
    def fake_status(_cur, _login):
        return {
            "setup_completed": True,
            "completed_at": "2026-03-21T19:10:00",
            "completed_by": "admin",
        }

    monkeypatch.setattr(usuarios_router, "db_transaction", fake_db_transaction)
    monkeypatch.setattr(usuarios_router, "obter_setup_status_tx", fake_status)
    app.dependency_overrides[get_current_user] = lambda: {"login": "admin", "perfil": "admin"}
    try:
        client = TestClient(app)
        response = client.get("/setup-status")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["setup_completed"] is True
    assert response.json()["completed_by"] == "admin"


def test_setup_status_usuario_nao_admin_retorna_403(monkeypatch):
    def fake_status(_cur, _login):
        raise AuthzError("Sem permissão. Perfil atual: user")

    monkeypatch.setattr(usuarios_router, "db_transaction", fake_db_transaction)
    monkeypatch.setattr(usuarios_router, "obter_setup_status_tx", fake_status)
    app.dependency_overrides[get_current_user] = lambda: {"login": "operador", "perfil": "user"}
    try:
        client = TestClient(app)
        response = client.get("/setup-status")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["code"] == "AUTHZ_ERROR"
