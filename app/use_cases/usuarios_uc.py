from app.core.exceptions import AuthzError, BusinessError
from app.core.security import hash_password
from app.infra.repositories.app_setup_repo import (
    app_setup_is_completed_tx,
    app_setup_mark_completed_tx,
    app_setup_status_tx,
)
from app.infra.repositories.logs_repo import log_tx
from app.infra.repositories.usuarios_repo import inserir_usuario_tx, obter_perfil_tx, usuarios_existem_tx


def exigir_perfil_tx(cur, login: str, perfis: set[str]) -> str:
    perfil = obter_perfil_tx(cur, login)
    if not perfil:
        raise BusinessError("Usuário não encontrado")
    if perfil not in perfis:
        raise AuthzError(f"Sem permissão. Perfil atual: {perfil}")
    return perfil


def criar_usuario_bootstrap_tx(cur, login: str, senha: str) -> None:
    """
    One-time setup policy:
    - The route layer must only expose/bootstrap this flow in setup/development.
    - Setup completion is persisted in the database and blocks future bootstrap attempts.
    - Once any user exists, bootstrap is irreversibly blocked by business rule.
    """
    if app_setup_is_completed_tx(cur):
        raise BusinessError("Bootstrap bloqueado: setup inicial já foi concluído.")
    if usuarios_existem_tx(cur):
        raise BusinessError("Bootstrap bloqueado: já existem usuários.")
    inserir_usuario_tx(cur, login, hash_password(senha), "admin")
    app_setup_mark_completed_tx(cur, login)
    log_tx(cur, login, "Bootstrap admin criado")


def criar_usuario_tx(cur, admin_login: str, login: str, senha: str, perfil: str) -> None:
    exigir_perfil_tx(cur, admin_login, {"admin"})
    inserir_usuario_tx(cur, login, hash_password(senha), perfil)
    log_tx(cur, admin_login, f"Usuário criado: {login} (perfil={perfil})")


def obter_setup_status_tx(cur, admin_login: str) -> dict:
    exigir_perfil_tx(cur, admin_login, {"admin"})
    return app_setup_status_tx(cur)
