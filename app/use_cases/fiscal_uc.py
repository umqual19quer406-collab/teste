from app.core.exceptions import BusinessError
from app.use_cases.usuarios_uc import exigir_perfil_tx

from app.infra.repositories.fiscal_repo import (
    fiscal_upsert_tx,
    fiscal_get_tes_tx,
    fiscal_listar_tx,
    fiscal_inativar_tx,
)


def sf4_salvar_uc_tx(
    cur,
    usuario: str,
    filial: str,
    tes_cod: str,
    cfop: str,
    icms: float,
    ipi: float,
    tipo: str = "S",
    pis: float = 0.0,
    cofins: float = 0.0,
    icms_st: float = 0.0,
    difal: float = 0.0,
    cst_icms: str | None = None,
    csosn: str | None = None,
    cst_pis: str | None = None,
    cst_cofins: str | None = None,
    gera_tit: bool = True,
    gera_est: bool = True,
    descr: str | None = None,
) -> dict:
    exigir_perfil_tx(cur, usuario, {"admin"})
    def _norm_code(v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        if not s or s.lower() in {"null", "none"}:
            return None
        return s

    cst_icms = _norm_code(cst_icms)
    csosn = _norm_code(csosn)
    cst_pis = _norm_code(cst_pis)
    cst_cofins = _norm_code(cst_cofins)
    fiscal_upsert_tx(
        cur,
        filial=filial,
        tes_cod=tes_cod,
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
        tipo=tipo,
        gera_tit=gera_tit,
        gera_est=gera_est,
        descr=descr,
    )
    return fiscal_get_tes_tx(cur, filial=filial, tes_cod=tes_cod)


def sf4_listar_uc_tx(cur, usuario: str, filial: str, ativos: bool = True):
    exigir_perfil_tx(cur, usuario, {"admin", "operador"})
    return fiscal_listar_tx(cur, filial=filial, ativo=ativos)


def sf4_inativar_uc_tx(cur, usuario: str, filial: str, tes_cod: str):
    exigir_perfil_tx(cur, usuario, {"admin"})
    fiscal_inativar_tx(cur, filial=filial, tes_cod=tes_cod, usuario=usuario)
    return {"filial": filial, "tes_cod": tes_cod, "ativo": False}
