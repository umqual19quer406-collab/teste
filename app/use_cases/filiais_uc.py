from app.use_cases.usuarios_uc import exigir_perfil_tx
from app.infra.repositories.sm0_repo import (
    sm0_listar_tx,
    sm0_criar_tx,
    sm0_inativar_tx,
)
from app.infra.repositories.serie_repo import seed_series_basicas_tx


def filiais_listar_uc_tx(cur, usuario: str):
    exigir_perfil_tx(cur, usuario, {"admin", "operador"})
    return sm0_listar_tx(cur)


def filiais_criar_uc_tx(
    cur,
    usuario: str,
    filial: str,
    serie_nf: str | None,
    serie_ar: str | None,
    serie_ap: str | None,
):
    exigir_perfil_tx(cur, usuario, {"admin"})
    sm0_criar_tx(cur, filial=filial, serie_nf=serie_nf, serie_ar=serie_ar, serie_ap=serie_ap)
    seed_series_basicas_tx(cur, filial=filial)
    return {"filial": filial}


def filiais_inativar_uc_tx(cur, usuario: str, filial: str):
    exigir_perfil_tx(cur, usuario, {"admin"})
    sm0_inativar_tx(cur, filial=filial)
    return {"filial": filial, "ativo": False}
