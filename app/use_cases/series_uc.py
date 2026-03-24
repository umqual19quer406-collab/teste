from app.core.exceptions import BusinessError
from app.use_cases.usuarios_uc import exigir_perfil_tx

from app.infra.repositories.sm0_repo import sm0_obter_series_tx, sm0_definir_series_tx
from app.infra.repositories.serie_repo import resolve_serie_tx, seed_series_basicas_tx, validar_serie_tx
from app.infra.repositories.sx5_repo import sx5_listar_tx, sx5_obter_tx, sx5_criar_tx


def series_obter_uc_tx(cur, usuario: str, filial: str) -> dict:
    exigir_perfil_tx(cur, usuario, {"admin", "operador"})
    seed_series_basicas_tx(cur, filial)
    sm0 = sm0_obter_series_tx(cur, filial)
    return {
        "filial": filial,
        "sm0": sm0,
        "serie_nf": resolve_serie_tx(cur, filial, "NF"),
        "serie_ar": resolve_serie_tx(cur, filial, "AR"),
        "serie_ap": resolve_serie_tx(cur, filial, "AP"),
    }


def series_definir_uc_tx(cur, usuario: str, filial: str, serie_nf: str | None, serie_ar: str | None, serie_ap: str | None):
    exigir_perfil_tx(cur, usuario, {"admin"})
    if serie_nf is not None and not str(serie_nf).strip():
        raise BusinessError("Série NF inválida")
    if serie_ar is not None and not str(serie_ar).strip():
        raise BusinessError("Série AR inválida")
    if serie_ap is not None and not str(serie_ap).strip():
        raise BusinessError("Série AP inválida")

    # garante SX5 para as séries informadas
    if serie_nf is not None:
        if sx5_obter_tx(cur, filial=filial, tabela="SERIE", chave="NF") is None:
            sx5_criar_tx(cur, filial=filial, tabela="SERIE", chave="NF", descr=str(serie_nf).strip(), ativo=True)
        validar_serie_tx(cur, filial=filial, tabela="NF", serie=str(serie_nf).strip())
    if serie_ar is not None:
        if sx5_obter_tx(cur, filial=filial, tabela="SERIE", chave="AR") is None:
            sx5_criar_tx(cur, filial=filial, tabela="SERIE", chave="AR", descr=str(serie_ar).strip(), ativo=True)
        validar_serie_tx(cur, filial=filial, tabela="AR", serie=str(serie_ar).strip())
    if serie_ap is not None:
        if sx5_obter_tx(cur, filial=filial, tabela="SERIE", chave="AP") is None:
            sx5_criar_tx(cur, filial=filial, tabela="SERIE", chave="AP", descr=str(serie_ap).strip(), ativo=True)
        validar_serie_tx(cur, filial=filial, tabela="AP", serie=str(serie_ap).strip())

    sm0_definir_series_tx(cur, filial, serie_nf=serie_nf, serie_ar=serie_ar, serie_ap=serie_ap)
    return series_obter_uc_tx(cur, usuario, filial)


def series_listar_sx5_uc_tx(cur, usuario: str, filial: str):
    exigir_perfil_tx(cur, usuario, {"admin", "operador"})
    seed_series_basicas_tx(cur, filial)
    return sx5_listar_tx(cur, filial=filial, tabela="SERIE", ativos=True)


def series_reset_uc_tx(cur, usuario: str, filial: str):
    exigir_perfil_tx(cur, usuario, {"admin"})
    # garante SX5 básico e valida antes de resetar
    seed_series_basicas_tx(cur, filial)
    validar_serie_tx(cur, filial, "NF", "1")
    validar_serie_tx(cur, filial, "AR", "1")
    validar_serie_tx(cur, filial, "AP", "1")
    sm0_definir_series_tx(cur, filial, serie_nf="1", serie_ar="1", serie_ap="1")
    return series_obter_uc_tx(cur, usuario, filial)
