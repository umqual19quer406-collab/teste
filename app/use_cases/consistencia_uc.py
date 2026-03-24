from datetime import date
from app.use_cases.usuarios_uc import exigir_perfil_tx
from app.infra.repositories.relatorios_repo import consistencia_fiscal_tx


def consistencia_fiscal_uc_tx(
    cur,
    usuario: str,
    filial: str,
    de: date | None,
    ate: date | None,
    limit: int = 200,
) -> dict:
    exigir_perfil_tx(cur, usuario, {"admin", "operador"})
    return consistencia_fiscal_tx(
        cur,
        filial=filial,
        de=de,
        ate=ate,
        limit=int(limit),
    )
