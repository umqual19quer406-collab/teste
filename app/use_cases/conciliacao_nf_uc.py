from datetime import date
from app.use_cases.usuarios_uc import exigir_perfil_tx
from app.infra.repositories.relatorios_repo import conciliacao_nf_financeiro_tx


def conciliacao_nf_financeiro_uc_tx(
    cur,
    usuario: str,
    filial: str,
    de: date | None,
    ate: date | None,
    tolerancia: float = 0.01,
    limit: int = 200,
) -> dict:
    exigir_perfil_tx(cur, usuario, {"admin", "operador"})
    return conciliacao_nf_financeiro_tx(
        cur,
        filial=filial,
        de=de,
        ate=ate,
        tolerancia=float(tolerancia),
        limit=int(limit),
    )
