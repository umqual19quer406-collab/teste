from app.infra.repositories.logs_repo import listar_logs_tx
from app.infra.repositories.usuarios_repo import obter_perfil_tx


def listar_logs_uc_tx(cur, usuario: str) -> list[dict]:
    perfil = obter_perfil_tx(cur, usuario) or ""
    return listar_logs_tx(cur, usuario, perfil)
