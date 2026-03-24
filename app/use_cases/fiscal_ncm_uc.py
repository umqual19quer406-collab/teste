from app.use_cases.usuarios_uc import exigir_perfil_tx
from app.infra.repositories.fiscal_ncm_repo import ncm_listar_tx, ncm_upsert_tx


def ncm_listar_uc_tx(cur, usuario: str, filial: str, ativos: bool = True):
    exigir_perfil_tx(cur, usuario, {"admin", "operador"})
    return ncm_listar_tx(cur, filial=filial, ativos=ativos)


def ncm_salvar_uc_tx(
    cur,
    usuario: str,
    filial: str,
    ncm: str,
    cfop: str,
    icms: float | None,
    ipi: float | None,
    ativo: bool = True,
):
    exigir_perfil_tx(cur, usuario, {"admin"})
    ncm_upsert_tx(
        cur,
        filial=filial,
        ncm=ncm,
        cfop=cfop,
        icms=icms,
        ipi=ipi,
        ativo=ativo,
    )
    return {"filial": filial, "ncm": ncm}
