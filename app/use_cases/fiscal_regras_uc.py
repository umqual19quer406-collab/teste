from app.use_cases.usuarios_uc import exigir_perfil_tx
from app.infra.repositories.fiscal_repo import (
    fiscal_regra_listar_tx,
    fiscal_regra_upsert_tx,
    fiscal_regra_inativar_tx,
)


def fiscal_regra_listar_uc_tx(
    cur,
    usuario: str,
    filial: str,
    tes_cod: str | None = None,
    cliente_cod: str | None = None,
    produto: str | None = None,
    ativos: bool = True,
):
    exigir_perfil_tx(cur, usuario, {"admin", "operador"})
    return fiscal_regra_listar_tx(
        cur,
        filial=filial,
        tes_cod=tes_cod,
        cliente_cod=cliente_cod,
        produto=produto,
        ativos=ativos,
    )


def fiscal_regra_salvar_uc_tx(
    cur,
    usuario: str,
    filial: str,
    tes_cod: str,
    cliente_cod: str | None,
    produto: str | None,
    cfop: str | None,
    icms: float | None,
    ipi: float | None,
    pis: float | None = None,
    cofins: float | None = None,
    icms_st: float | None = None,
    difal: float | None = None,
    cst_icms: str | None = None,
    csosn: str | None = None,
    cst_pis: str | None = None,
    cst_cofins: str | None = None,
    gera_tit: bool | None = None,
    gera_est: bool | None = None,
    prioridade: int = 0,
    ativo: bool = True,
    regra_id: int | None = None,
) -> dict:
    exigir_perfil_tx(cur, usuario, {"admin"})
    regra_id = fiscal_regra_upsert_tx(
        cur,
        filial=filial,
        tes_cod=tes_cod,
        cliente_cod=cliente_cod,
        produto=produto,
        cfop=cfop,
        icms=icms,
        ipi=ipi,
        pis=pis,
        cofins=cofins,
        icms_st=icms_st,
        difal=difal,
        cst_icms=cst_icms,
        csosn=csosn,
        cst_pis=cst_pis,
        cst_cofins=cst_cofins,
        gera_tit=gera_tit,
        gera_est=gera_est,
        prioridade=prioridade,
        ativo=ativo,
        regra_id=regra_id,
    )
    return {"id": int(regra_id), "filial": filial, "tes_cod": tes_cod}


def fiscal_regra_inativar_uc_tx(cur, usuario: str, regra_id: int):
    exigir_perfil_tx(cur, usuario, {"admin"})
    fiscal_regra_inativar_tx(cur, regra_id=int(regra_id))
    return {"id": int(regra_id), "ativo": False}
