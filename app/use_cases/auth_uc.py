import pyodbc

from app.domain.errors import AuthError
from app.infra.repositories.usuarios_repo import obter_usuario_por_login_tx
from app.security.passwords import verify_password


def autenticar_usuario_tx(cur: pyodbc.Cursor, username: str, password: str) -> dict:
    user = obter_usuario_por_login_tx(cur, username)
    if not user:
        raise AuthError("Credenciais invalidas")

    if not verify_password(password, user["U_SENHA_HASH"]):
        raise AuthError("Credenciais invalidas")

    return user
